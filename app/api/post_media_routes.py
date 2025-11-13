#THIS IS ONLY A JOINING TABLE FOR POSTS AND MEDIA I DON'T THINK WE NEED THIS TABLE 

"""
post_media_routes.py (post_media)

GET /api/posts/:post_id/media – list media attached to a post (ordered by sort_order). ok

POST /api/posts/:post_id/media – attach one/many media_ids[] (optional sort_order). ok 

PATCH /api/posts/:post_id/media/:media_id – update sort_order. ok

DELETE /api/posts/:post_id/media/:media_id – detach. ok

POST /api/posts/:post_id/media/reorder – bulk reorder [{"media_id","sort_order"}...]. ok
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Post, PostMedia, Media
from datetime import datetime

post_media_routes = Blueprint('post_media', __name__)

#! List Post Media ///////////////////////////////////////////////////////////////////////////
@post_media_routes.route('/posts/<int:post_id>/media', methods=['GET'])
@login_required
def get_post_media(post_id):
    """
    GET /api/posts/:post_id/media – list media attached to a post (ordered by sort_order)
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get post media with media details, ordered by sort_order
    post_media_list = db.session.query(PostMedia, Media).join(
        Media, PostMedia.media_id == Media.id
    ).filter(
        PostMedia.post_id == post_id
    ).order_by(
        PostMedia.sort_order.asc(),
        PostMedia.added_at.asc()
    ).all()

    # Format response with media details
    media_list = []
    for post_media, media in post_media_list:
        media_dict = media.to_dict()
        media_dict['sort_order'] = post_media.sort_order
        media_dict['added_at'] = post_media.added_at.isoformat() if post_media.added_at else None
        media_list.append(media_dict)

    return jsonify({
        'media': media_list,
        'total': len(media_list)
    })

#! Attach Media to Post ///////////////////////////////////////////////////////////////////////////
@post_media_routes.route('/posts/<int:post_id>/media', methods=['POST'])
@login_required
def attach_media_to_post(post_id):
    """
    POST /api/posts/:post_id/media – attach media with sort_order
    Body: [{"media_id": 1, "sort_order": 0}, {"media_id": 2, "sort_order": 1}, ...]
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    if not data or 'media_attachments' not in data:
        return jsonify({'error': 'media_attachments array is required'}), 400

    media_attachments = data['media_attachments']
    if not isinstance(media_attachments, list):
        return jsonify({'error': 'media_attachments must be an array'}), 400

    if not media_attachments:
        return jsonify({'error': 'media_attachments cannot be empty'}), 400

    # Validate the structure of each item
    for item in media_attachments:
        if not isinstance(item, dict) or 'media_id' not in item:
            return jsonify({'error': 'Each item must have media_id'}), 400
        
        try:
            int(item['media_id'])
            if 'sort_order' in item and item['sort_order'] is not None:
                int(item['sort_order'])
        except (ValueError, TypeError):
            return jsonify({'error': 'media_id and sort_order must be valid integers'}), 400

    # Extract media IDs and verify they belong to current user
    media_ids = [item['media_id'] for item in media_attachments]
    media_list = Media.query.filter(
        Media.id.in_(media_ids),
        Media.user_id == current_user.id
    ).all()

    if len(media_list) != len(media_ids):
        return jsonify({'error': 'Some media not found or not owned by user'}), 404

    created_attachments = []
    errors = []

    # First pass: validate all attachments and collect sort_orders
    attachments_to_create = []
    for item in media_attachments:
        media_id = item['media_id']
        sort_order = item.get('sort_order')
        
        try:
            # Check if attachment already exists
            existing = PostMedia.query.filter_by(
                post_id=post_id, 
                media_id=media_id
            ).first()
            
            if existing:
                errors.append(f'Media {media_id} is already attached to this post')
                continue

            attachments_to_create.append({
                'media_id': media_id,
                'sort_order': sort_order
            })

        except Exception as e:
            errors.append(f'Error validating media {media_id}: {str(e)}')

    if errors and not attachments_to_create:
        return jsonify({'error': 'Failed to attach media', 'details': errors}), 400

    try:
        # Second pass: handle atomic shifting for each attachment
        for attachment_data in attachments_to_create:
            media_id = attachment_data['media_id']
            sort_order = attachment_data['sort_order']
            
            # If sort_order is specified and not None, shift existing items
            if sort_order is not None:
                # Check if any existing media has this sort_order
                existing_with_order = PostMedia.query.filter_by(
                    post_id=post_id,
                    sort_order=sort_order
                ).first()
                
                if existing_with_order:
                    # Shift all items with sort_order >= new_sort_order by +1
                    PostMedia.query.filter(
                        PostMedia.post_id == post_id,
                        PostMedia.sort_order >= sort_order
                    ).update({PostMedia.sort_order: PostMedia.sort_order + 1})

            # Create post media attachment
            post_media = PostMedia(
                post_id=post_id,
                media_id=media_id,
                sort_order=sort_order
            )

            db.session.add(post_media)
            created_attachments.append(post_media)

        db.session.commit()
        
        # Fetch the complete media objects with their details
        attached_media = []
        for attachment in created_attachments:
            media = Media.query.get(attachment.media_id)
            if media:
                media_dict = media.to_dict()
                media_dict['sort_order'] = attachment.sort_order
                media_dict['added_at'] = attachment.added_at.isoformat() if attachment.added_at else None
                attached_media.append(media_dict)
        
        return jsonify({
            'message': f'Successfully attached {len(created_attachments)} media items',
            'media': attached_media,
            'errors': errors if errors else None
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save media attachments'}), 500

#! Update Sort Order ///////////////////////////////////////////////////////////////////////////
@post_media_routes.route('/posts/<int:post_id>/media/<int:media_id>', methods=['PATCH'])
@login_required
def update_media_sort_order(post_id, media_id):
    """
    PATCH /api/posts/:post_id/media/:media_id – update sort_order with atomic shifting
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Verify media exists and belongs to current user
    media = Media.query.filter_by(id=media_id, user_id=current_user.id).first()
    if not media:
        return jsonify({'error': 'Media not found'}), 404

    # Find the post media attachment
    post_media = PostMedia.query.filter_by(
        post_id=post_id, 
        media_id=media_id
    ).first()
    
    if not post_media:
        return jsonify({'error': 'Media is not attached to this post'}), 404

    data = request.get_json()
    if not data or 'sort_order' not in data:
        return jsonify({'error': 'sort_order is required'}), 400

    new_sort_order = data['sort_order']
    if not isinstance(new_sort_order, int) and new_sort_order is not None:
        return jsonify({'error': 'sort_order must be an integer or null'}), 400

    old_sort_order = post_media.sort_order

    # If sort_order hasn't changed, no need to do anything
    if old_sort_order == new_sort_order:
        return jsonify({
            'message': 'Sort order unchanged',
            'post_media': post_media.to_dict()
        })

    try:
        # Atomic shifting logic to maintain clean indices
        if new_sort_order is not None and old_sort_order is not None:
            if new_sort_order < old_sort_order:
                # Moving to earlier position: increment items in [new_sort_order, old_sort_order-1]
                PostMedia.query.filter(
                    PostMedia.post_id == post_id,
                    PostMedia.media_id != media_id,  # Exclude the item being moved
                    PostMedia.sort_order >= new_sort_order,
                    PostMedia.sort_order < old_sort_order
                ).update({PostMedia.sort_order: PostMedia.sort_order + 1})
                
            elif new_sort_order > old_sort_order:
                # Moving to later position: decrement items in [old_sort_order+1, new_sort_order]
                PostMedia.query.filter(
                    PostMedia.post_id == post_id,
                    PostMedia.media_id != media_id,  # Exclude the item being moved
                    PostMedia.sort_order > old_sort_order,
                    PostMedia.sort_order <= new_sort_order
                ).update({PostMedia.sort_order: PostMedia.sort_order - 1})

        # Set the new sort_order for the moved item
        post_media.sort_order = new_sort_order
        
        db.session.commit()

        return jsonify({
            'message': 'Sort order updated successfully with atomic shifting',
            'post_media': post_media.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update sort order'}), 500

#! Detach Media from Post ///////////////////////////////////////////////////////////////////////////
@post_media_routes.route('/posts/<int:post_id>/media/<int:media_id>', methods=['DELETE'])
@login_required
def detach_media_from_post(post_id, media_id):
    """
    DELETE /api/posts/:post_id/media/:media_id – detach media from post
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Verify media exists and belongs to current user
    media = Media.query.filter_by(id=media_id, user_id=current_user.id).first()
    if not media:
        return jsonify({'error': 'Media not found'}), 404

    # Find the post media attachment
    post_media = PostMedia.query.filter_by(
        post_id=post_id, 
        media_id=media_id
    ).first()
    
    if not post_media:
        return jsonify({'error': 'Media is not attached to this post'}), 404

    try:
        db.session.delete(post_media)
        db.session.commit()

        return jsonify({'message': 'Media detached successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to detach media'}), 500

#! Bulk Reorder Media ///////////////////////////////////////////////////////////////////////////
@post_media_routes.route('/posts/<int:post_id>/media/reorder', methods=['POST'])
@login_required
def reorder_post_media(post_id):
    """
    POST /api/posts/:post_id/media/reorder – bulk reorder media
    Body: {"media_orders": [{"media_id": 1, "sort_order": 0}, {"media_id": 2, "sort_order": 1}, ...]}
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    if not data or 'media_orders' not in data:
        return jsonify({'error': 'media_orders array is required'}), 400

    media_orders = data['media_orders']
    if not isinstance(media_orders, list):
        return jsonify({'error': 'media_orders must be an array'}), 400

    if not media_orders:
        return jsonify({'error': 'media_orders cannot be empty'}), 400

    # Validate the structure of each item
    for item in media_orders:
        if not isinstance(item, dict) or 'media_id' not in item or 'sort_order' not in item:
            return jsonify({'error': 'Each item must have media_id and sort_order'}), 400
        
        try:
            int(item['media_id'])
            int(item['sort_order']) if item['sort_order'] is not None else None
        except (ValueError, TypeError):
            return jsonify({'error': 'media_id and sort_order must be valid integers'}), 400

    # Extract media IDs and verify they belong to current user
    media_ids = [item['media_id'] for item in media_orders]
    media_list = Media.query.filter(
        Media.id.in_(media_ids),
        Media.user_id == current_user.id
    ).all()

    if len(media_list) != len(media_ids):
        return jsonify({'error': 'Some media not found or not owned by user'}), 404

    # Verify all media are attached to the post
    existing_attachments = PostMedia.query.filter(
        PostMedia.post_id == post_id,
        PostMedia.media_id.in_(media_ids)
    ).all()

    existing_media_ids = {pm.media_id for pm in existing_attachments}
    requested_media_ids = set(media_ids)

    if existing_media_ids != requested_media_ids:
        missing_ids = requested_media_ids - existing_media_ids
        return jsonify({'error': f'Media {list(missing_ids)} are not attached to this post'}), 404

    try:
        # First, get all current sort_orders to track changes
        current_media_orders = {}
        for pm in existing_attachments:
            current_media_orders[pm.media_id] = pm.sort_order
        
        # Create a mapping of media_id to new sort_order
        new_orders = {item['media_id']: item['sort_order'] for item in media_orders}
        
        # Identify which items are actually changing position
        changes = []
        for media_id, new_order in new_orders.items():
            old_order = current_media_orders.get(media_id)
            if old_order != new_order:
                changes.append({
                    'media_id': media_id,
                    'old_order': old_order,
                    'new_order': new_order
                })
        
        # Sort changes by new_order to process them in order
        changes.sort(key=lambda x: x['new_order'] if x['new_order'] is not None else float('inf'))
        
        # Process each change with atomic shifting
        for change in changes:
            media_id = change['media_id']
            old_order = change['old_order']
            new_order = change['new_order']
            
            if old_order is not None and new_order is not None:
                if new_order < old_order:
                    # Moving to earlier position: increment items in [new_order, old_order-1]
                    PostMedia.query.filter(
                        PostMedia.post_id == post_id,
                        PostMedia.media_id != media_id,  # Exclude the item being moved
                        PostMedia.sort_order >= new_order,
                        PostMedia.sort_order < old_order
                    ).update({PostMedia.sort_order: PostMedia.sort_order + 1})
                    
                elif new_order > old_order:
                    # Moving to later position: decrement items in [old_order+1, new_order]
                    PostMedia.query.filter(
                        PostMedia.post_id == post_id,
                        PostMedia.media_id != media_id,  # Exclude the item being moved
                        PostMedia.sort_order > old_order,
                        PostMedia.sort_order <= new_order
                    ).update({PostMedia.sort_order: PostMedia.sort_order - 1})
            
            # Set the new sort_order for the moved item
            post_media = PostMedia.query.filter_by(
                post_id=post_id,
                media_id=media_id
            ).first()
            
            if post_media:
                post_media.sort_order = new_order

        db.session.commit()

        return jsonify({
            'message': f'Successfully reordered {len(changes)} media items with atomic shifting',
            'updated_count': len(changes),
            'changes': changes
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reorder media'}), 500