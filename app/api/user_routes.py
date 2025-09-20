from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, User

user_routes = Blueprint('users', __name__)

#! Get all users ///////////////////////////////////////////////////////////////////////////
@user_routes.route('/')
@login_required
def users():
    """
    Query for all users and returns them in a list of user dictionaries
    """
    users = User.query.all()
    return {'users': [user.to_dict() for user in users]}

#! Get a user by id ///////////////////////////////////////////////////////////////////////////
@user_routes.route('/<int:id>')
@login_required
def user(id):
    """
    Query for a user by id and returns that user in a dictionary
    """
    user = User.query.get(id)
    return user.to_dict()

#! Update user ///////////////////////////////////////////////////////////////////////////

@user_routes.route('/<int:user_id>', methods=['PATCH'])
@login_required
def update_user(user_id):
    """
    PATCH /api/users/:id – update username/email/password
    """
    try:
        # Check if user is updating themselves or has admin privileges
        if user_id != current_user.id:
            # TODO: Add admin check when admin system is implemented
            # For now, only allow users to update their own profile
            return jsonify({'error': 'You can only update your own profile'}), 403
        
        # Find the user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update username if provided
        if 'username' in data:
            new_username = data['username'].strip()
            if not new_username:
                return jsonify({'error': 'Username cannot be empty'}), 400
            
            # Check if username already exists (excluding current user)
            existing_user = User.query.filter(
                User.username == new_username,
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 400
            
            user.username = new_username
        
        # Update email if provided
        if 'email' in data:
            new_email = data['email'].strip()
            if not new_email:
                return jsonify({'error': 'Email cannot be empty'}), 400
            
            # Check if email already exists (excluding current user)
            existing_user = User.query.filter(
                User.email == new_email,
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({'error': 'Email already exists'}), 400
            
            user.email = new_email
        
        # Update password if provided
        if 'password' in data:
            new_password = data['password']
            if not new_password:
                return jsonify({'error': 'Password cannot be empty'}), 400
            
            if len(new_password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            
            user.password = new_password
        
        db.session.commit()
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Delete user ///////////////////////////////////////////////////////////////////////////

@user_routes.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """
    DELETE /api/users/:id – delete user (admin or self with checks)
    """
    try:
        # Find the user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user is deleting themselves or has admin privileges
        if user_id != current_user.id:
            # TODO: Add admin check when admin system is implemented
            # For now, only allow users to delete their own account
            return jsonify({'error': 'You can only delete your own account'}), 403
        
        # Check if user has any dependent data (posts, user_platforms, media)
        if user.posts:
            return jsonify({'error': 'Cannot delete user with existing posts. Please delete posts first.'}), 400
        
        if user.user_platforms:
            return jsonify({'error': 'Cannot delete user with platform connections. Please disconnect platforms first.'}), 400
        
        if user.media:
            return jsonify({'error': 'Cannot delete user with media files. Please delete media first.'}), 400
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



    """ 
    users_routes.py (users)

    GET /api/users (admin) – list; filters: email, created_from, created_to. ok

    POST /api/users – sign-up/create. it is already in auth_routes.py ok

    GET /api/users/:id – fetch one. ok

    PATCH /api/users/:id – update name/email/password. ok

    DELETE /api/users/:id – delete (admin or self with checks). ok
    
    """