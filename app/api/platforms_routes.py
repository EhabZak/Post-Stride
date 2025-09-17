"""
platforms_routes.py (social_platforms) 

GET /api/platforms – list; optional q (name), sort. ok

GET /api/platforms/:id – fetch one. ok

(admin) POST /api/platforms – create. ok

(admin) PATCH /api/platforms/:id – update. ok

(admin) DELETE /api/platforms/:id – delete. ok

"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, SocialPlatform
from datetime import datetime

platforms_routes = Blueprint('platforms', __name__)

def is_admin(user):
    """
    Check if user has admin privileges
    TODO: Implement proper admin role system
    """
    # For now, return True for all users - implement proper admin check later
    # This could check user.role == 'admin' or user.is_admin == True
    return True

#! Get all platforms ///////////////////////////////////////////////////////////////////////////

@platforms_routes.route('', methods=['GET'])
@login_required
def get_platforms():
    """
    GET /api/platforms – list platforms with optional search and sort
    """
    try:
        # Get query parameters
        q = request.args.get('q')  # search by name
        sort_by = request.args.get('sort', 'name')  # default sort by name
        
        # Start with base query
        query = SocialPlatform.query
        
        # Apply search filter
        if q:
            query = query.filter(SocialPlatform.name.ilike(f'%{q}%'))
        
        # Apply sorting
        if sort_by == 'name':
            query = query.order_by(SocialPlatform.name.asc())
        elif sort_by == 'created_at':
            query = query.order_by(SocialPlatform.created_at.desc())
        else:
            return jsonify({'error': 'Invalid sort parameter. Use: name or created_at.'}), 400
        
        # Execute query
        platforms = query.all()
        
        # Convert to dictionary format
        platforms_data = [platform.to_dict() for platform in platforms]
        
        return jsonify({'platforms': platforms_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#! Get a platform by id ///////////////////////////////////////////////////////////////////////////

@platforms_routes.route('/<int:platform_id>', methods=['GET'])
@login_required
def get_platform(platform_id):
    """
    GET /api/platforms/:id – fetch one platform
    """
    try:
        # Find platform
        platform = SocialPlatform.query.get(platform_id)
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        return jsonify({'platform': platform.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#! Create a platform (admin) ///////////////////////////////////////////////////////////////////////////

@platforms_routes.route('', methods=['POST'])
@login_required
def create_platform():
    """
    POST /api/platforms – create a new platform (admin only)
    """
    try:
        # Check admin privileges
        if not is_admin(current_user):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
        
        name = data['name'].strip()
        api_base_url = data.get('api_base_url', '').strip() if data.get('api_base_url') else None
        
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400
        
        # Check if platform with same name already exists
        existing_platform = SocialPlatform.query.filter_by(name=name).first()
        if existing_platform:
            return jsonify({'error': 'Platform with this name already exists'}), 400
        
        # Create new platform
        new_platform = SocialPlatform(
            name=name,
            api_base_url=api_base_url
        )
        
        db.session.add(new_platform)
        db.session.commit()
        
        return jsonify({'platform': new_platform.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Update a platform (admin) ///////////////////////////////////////////////////////////////////////////

@platforms_routes.route('/<int:platform_id>', methods=['PATCH'])
@login_required
def update_platform(platform_id):
    """
    PATCH /api/platforms/:id – update a platform (admin only)
    """
    try:
        # Check admin privileges
        if not is_admin(current_user):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Find platform
        platform = SocialPlatform.query.get(platform_id)
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update name if provided
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({'error': 'Name cannot be empty'}), 400
            
            # Check if another platform with same name exists
            existing_platform = SocialPlatform.query.filter(
                SocialPlatform.name == name,
                SocialPlatform.id != platform_id
            ).first()
            if existing_platform:
                return jsonify({'error': 'Platform with this name already exists'}), 400
            
            platform.name = name
        
        # Update api_base_url if provided
        if 'api_base_url' in data:
            platform.api_base_url = data['api_base_url'].strip() if data['api_base_url'] else None
        
        db.session.commit()
        
        return jsonify({'platform': platform.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Delete a platform (admin) ///////////////////////////////////////////////////////////////////////////

@platforms_routes.route('/<int:platform_id>', methods=['DELETE'])
@login_required
def delete_platform(platform_id):
    """
    DELETE /api/platforms/:id – delete a platform (admin only)
    """
    try:
        # Check admin privileges
        if not is_admin(current_user):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Find platform
        platform = SocialPlatform.query.get(platform_id)
        
        if not platform:
            return jsonify({'error': 'Platform not found'}), 404
        
        # Check if platform is being used
        if platform.user_platforms or platform.post_platforms:
            return jsonify({'error': 'Cannot delete platform that is being used by users or posts'}), 400
        
        # Delete the platform
        db.session.delete(platform)
        db.session.commit()
        
        return jsonify({'message': 'Platform deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500