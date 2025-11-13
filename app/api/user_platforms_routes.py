


from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, UserPlatform, SocialPlatform
from app.utils.encryption import mask_token
from datetime import datetime, timezone
import re

user_platforms_routes = Blueprint('user_platforms', __name__)
#! helper functions ///////////////////////////////////////////////////////////////////////////
def parse_iso_datetime(datetime_str):
    """
    Parse ISO 8601 datetime string, handling 'Z' suffix for UTC
    Returns a timezone-naive UTC datetime for database storage
    """
    if not datetime_str:
        return None
    
    # Replace 'Z' with '+00:00' for UTC timezone
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1] + '+00:00'
    
    try:
        dt = datetime.fromisoformat(datetime_str)
        # Convert to UTC and make timezone-naive for database storage
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        raise ValueError(f"Invalid datetime format: {datetime_str}")

def is_token_expired(token_expiry):
    """
    Check if token is expired
    """
    if not token_expiry:
        return True
    return token_expiry <= datetime.utcnow()

def get_token_status(token_expiry):
    """
    Get token status: active or expired
    """
    return 'expired' if is_token_expired(token_expiry) else 'active'

#! Get all user platforms ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('', methods=['GET'])
@login_required
def get_user_platforms():
    """
    GET /api/user-platforms – list current user's connections with filters
    """
    try:
        # Get query parameters
        platform_id = request.args.get('platform_id')
        expires_before = request.args.get('expires_before')
        status = request.args.get('status')  # active or expired
        
        # Start with base query for current user
        query = UserPlatform.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if platform_id:
            try:
                platform_id = int(platform_id)
                query = query.filter(UserPlatform.platform_id == platform_id)
            except ValueError:
                return jsonify({'error': 'Invalid platform_id. Must be an integer.'}), 400
        
        if expires_before:
            try:
                expires_before_dt = parse_iso_datetime(expires_before)
                query = query.filter(UserPlatform.token_expiry <= expires_before_dt)
            except ValueError:
                return jsonify({'error': 'Invalid expires_before format. Use ISO format.'}), 400
        
        if status:
            if status not in ['active', 'expired']:
                return jsonify({'error': 'Invalid status. Must be "active" or "expired".'}), 400
            
            now = datetime.utcnow()
            if status == 'active':
                query = query.filter(UserPlatform.token_expiry > now)
            else:  # expired
                query = query.filter(UserPlatform.token_expiry <= now)
        
        # Execute query
        user_platforms = query.all()
        
        # Convert to dictionary format with additional info
        platforms_data = []
        for user_platform in user_platforms:
            platform_data = user_platform.to_dict(include_tokens=False)  # Use masked tokens
            
            # Add platform information
            platform_data['platform_name'] = user_platform.platform.name
            
            # Add token status
            platform_data['token_status'] = get_token_status(user_platform.token_expiry)
            
            platforms_data.append(platform_data)
        
        return jsonify({'user_platforms': platforms_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#! Create user platform connection ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('', methods=['POST'])
@login_required
def create_user_platform():
    """
    POST /api/user-platforms – connect/create user platform with tokens
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'platform_id' not in data:
            return jsonify({'error': 'platform_id is required'}), 400
        
        platform_id = data['platform_id']
        platform_user_id = data.get('platform_user_id')
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        token_expiry = data.get('token_expiry')
        
        # Validate platform exists
        platform = SocialPlatform.query.get(platform_id)
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        # Parse token_expiry if provided
        if token_expiry:
            try:
                token_expiry = parse_iso_datetime(token_expiry)
            except ValueError:
                return jsonify({'error': 'Invalid token_expiry format. Use ISO format.'}), 400
        
        # Check for existing connection
        existing_connection = UserPlatform.query.filter_by(
            user_id=current_user.id,
            platform_id=platform_id,
            platform_user_id=platform_user_id
        ).first()
        
        if existing_connection:
            return jsonify({'error': 'Connection already exists for this platform and user ID'}), 400
        
        # Create new user platform connection
        new_user_platform = UserPlatform(
            user_id=current_user.id,
            platform_id=platform_id,
            platform_user_id=platform_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry
        )
        
        db.session.add(new_user_platform)
        db.session.commit()
        
        # Return created connection with platform info
        platform_data = new_user_platform.to_dict(include_tokens=False)  # Use masked tokens
        platform_data['platform_name'] = new_user_platform.platform.name
        platform_data['token_status'] = get_token_status(new_user_platform.token_expiry)
        
        return jsonify({'user_platform': platform_data}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Get user platform by id ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('/<int:user_platform_id>', methods=['GET'])
@login_required
def get_user_platform(user_platform_id):
    """
    GET /api/user-platforms/:id – fetch one user platform (ownership check)
    """
    try:
        # Find user platform belonging to current user
        user_platform = UserPlatform.query.filter_by(
            id=user_platform_id, 
            user_id=current_user.id
        ).first()
        
        if not user_platform:
            return jsonify({'error': 'User platform connection not found'}), 404
        
        # Return platform data with additional info
        platform_data = user_platform.to_dict(include_tokens=False)  # Use masked tokens
        platform_data['platform_name'] = user_platform.platform.name
        platform_data['token_status'] = get_token_status(user_platform.token_expiry)
        
        return jsonify({'user_platform': platform_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#! Update user platform ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('/<int:user_platform_id>', methods=['PATCH'])
@login_required
def update_user_platform(user_platform_id):
    """
    PATCH /api/user-platforms/:id – rotate tokens/update info
    """
    try:
        # Find user platform belonging to current user
        user_platform = UserPlatform.query.filter_by(
            id=user_platform_id, 
            user_id=current_user.id
        ).first()
        
        if not user_platform:
            return jsonify({'error': 'User platform connection not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update platform_user_id if provided
        if 'platform_user_id' in data:
            user_platform.platform_user_id = data['platform_user_id']
        
        # Update access_token if provided
        if 'access_token' in data:
            user_platform.access_token = data['access_token']
        
        # Update refresh_token if provided
        if 'refresh_token' in data:
            user_platform.refresh_token = data['refresh_token']
        
        # Update token_expiry if provided
        if 'token_expiry' in data:
            if data['token_expiry'] is None:
                user_platform.token_expiry = None
            else:
                try:
                    user_platform.token_expiry = parse_iso_datetime(data['token_expiry'])
                except ValueError:
                    return jsonify({'error': 'Invalid token_expiry format. Use ISO format.'}), 400
        
        # Update the updated_at timestamp
        user_platform.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Return updated platform data
        platform_data = user_platform.to_dict(include_tokens=False)  # Use masked tokens
        platform_data['platform_name'] = user_platform.platform.name
        platform_data['token_status'] = get_token_status(user_platform.token_expiry)
        
        return jsonify({'user_platform': platform_data}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Delete user platform ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('/<int:user_platform_id>', methods=['DELETE'])
@login_required
def delete_user_platform(user_platform_id):
    """
    DELETE /api/user-platforms/:id – disconnect user platform
    """
    try:
        # Find user platform belonging to current user
        user_platform = UserPlatform.query.filter_by(
            id=user_platform_id, 
            user_id=current_user.id
        ).first()
        
        if not user_platform:
            return jsonify({'error': 'User platform connection not found'}), 404
        
        # Delete the connection
        db.session.delete(user_platform)
        db.session.commit()
        
        return jsonify({'message': 'User platform connection deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Refresh token ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('/<int:user_platform_id>/refresh-token', methods=['POST'])
@login_required
def refresh_user_platform_token(user_platform_id):
    """
    POST /api/user-platforms/:id/refresh-token – force refresh token
    """
    try:
        # Find user platform belonging to current user
        user_platform = UserPlatform.query.filter_by(
            id=user_platform_id, 
            user_id=current_user.id
        ).first()
        
        if not user_platform:
            return jsonify({'error': 'User platform connection not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields for refresh
        if not data:
            return jsonify({'error': 'Token data is required'}), 400
        
        if 'access_token' not in data:
            return jsonify({'error': 'access_token is required'}), 400
        
        # Update tokens
        user_platform.access_token = data['access_token']
        
        if 'refresh_token' in data:
            user_platform.refresh_token = data['refresh_token']
        
        if 'token_expiry' in data:
            if data['token_expiry'] is None:
                user_platform.token_expiry = None
            else:
                try:
                    user_platform.token_expiry = parse_iso_datetime(data['token_expiry'])
                except ValueError:
                    return jsonify({'error': 'Invalid token_expiry format. Use ISO format.'}), 400
        
        # Update the updated_at timestamp
        user_platform.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Return updated platform data
        platform_data = user_platform.to_dict(include_tokens=False)  # Use masked tokens
        platform_data['platform_name'] = user_platform.platform.name
        platform_data['token_status'] = get_token_status(user_platform.token_expiry)
        
        return jsonify({'user_platform': platform_data}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Check duplicates ///////////////////////////////////////////////////////////////////////////

@user_platforms_routes.route('/check-duplicates', methods=['GET'])
@login_required
def check_duplicates():
    """
    GET /api/user-platforms/check-duplicates – pre-create uniqueness check
    """
    try:
        # Get query parameters
        platform_id = request.args.get('platform_id')
        platform_user_id = request.args.get('platform_user_id')
        
        if not platform_id:
            return jsonify({'error': 'platform_id is required'}), 400
        
        try:
            platform_id = int(platform_id)
        except ValueError:
            return jsonify({'error': 'Invalid platform_id. Must be an integer.'}), 400
        
        # Check for existing connection
        query = UserPlatform.query.filter_by(
            user_id=current_user.id,
            platform_id=platform_id
        )
        
        if platform_user_id:
            query = query.filter_by(platform_user_id=platform_user_id)
        
        existing_connection = query.first()
        
        if existing_connection:
            return jsonify({
                'exists': True,
                'message': 'Connection already exists for this platform',
                'existing_connection': {
                    'id': existing_connection.id,
                    'platform_user_id': existing_connection.platform_user_id,
                    'token_status': get_token_status(existing_connection.token_expiry)
                }
            }), 200
        else:
            return jsonify({
                'exists': False,
                'message': 'No existing connection found'
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


"""
user_platforms_routes.py (user_platforms)

GET /api/user-platforms – list current user's connections; filters: platform_id, expires_before, status=active|expired. ok

POST /api/user-platforms – connect/create (stores platform_user_id, tokens, expiry). ok

GET /api/user-platforms/:id – fetch one (ownership). ok

PATCH /api/user-platforms/:id – rotate tokens/update info. ok

DELETE /api/user-platforms/:id – disconnect. ok

POST /api/user-platforms/:id/refresh-token – force refresh. ok

GET /api/user-platforms/check-duplicates – pre-create uniqueness check. ok

"""
''' 
Also I need to do 
Security notes:

1-Encrypt access_token and refresh_token at rest (e.g., app-level AES-GCM with a KMS-managed key). ok

2-Never log raw tokens; mask to first/last 4 chars. ok

3-Store client secrets in env/secret manager, not the DB. ok

4-Add short timeouts + retries with jitter to avoid thundering herd near expiry. 

5-Failure/Recovery behavior (UX) 

6-If refresh fails: set needs_reconnect=true; show inline banner on the dashboard connection card: “Session expired—Reconnect.”

Allow a one-click OAuth re-connect to rebuild tokens without deleting the connection row.

'''