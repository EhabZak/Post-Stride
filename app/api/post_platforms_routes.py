"""
post_platforms_routes.py (post_platforms)

GET /api/posts/:post_id/platforms – list per-platform rows (filter status=pending|queued|publishing|published|failed|skipped). ok

POST /api/posts/:post_id/platforms – bulk attach platforms (create rows; allow per-platform caption/media). ok

GET /api/posts/:post_id/platforms/:platform_id – fetch one row.  ok

PATCH /api/posts/:post_id/platforms/:platform_id – update platform_caption, media_urls, or status. ok

DELETE /api/posts/:post_id/platforms/:platform_id – detach/dalete platform. ok 

POST /api/posts/:post_id/platforms/:platform_id/queue – set status=queued. ok

POST /api/posts/:post_id/platforms/:platform_id/retry – retry failed. ok

POST /api/posts/:post_id/platforms/:platform_id/cancel – set status=skipped cancel posting on a platform. ok

(ops) GET /api/post-platforms – cross-post view; filters: status, platform_id, published_from/to. ok

"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Post, PostPlatform, SocialPlatform
from datetime import datetime

post_platforms_routes = Blueprint('post_platforms', __name__)

#! List Post Platforms ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms', methods=['GET'])
@login_required
def get_post_platforms(post_id):
    """
    GET /api/posts/:post_id/platforms – list per-platform rows
    Filter by status: pending|queued|publishing|published|failed|skipped
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Get query parameters
    status = request.args.get('status')
    
    # Build query
    query = PostPlatform.query.filter_by(post_id=post_id)
    
    if status:
        valid_statuses = ['pending', 'queued', 'publishing', 'published', 'failed', 'skipped']
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        query = query.filter_by(status=status)
    
    post_platforms = query.all()
    
    return jsonify({
        'post_platforms': [pp.to_dict() for pp in post_platforms],
        'total': len(post_platforms)
    })

#! Bulk Attach Platforms ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms', methods=['POST'])
@login_required
def bulk_attach_platforms(post_id):
    """
    POST /api/posts/:post_id/platforms – bulk attach platforms
    Allow per-platform caption/media customization
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    if not data or 'platforms' not in data:
        return jsonify({'error': 'Platforms data is required'}), 400

    platforms_data = data['platforms']
    if not isinstance(platforms_data, list):
        return jsonify({'error': 'Platforms must be an array'}), 400

    created_platforms = []
    errors = []

    for platform_data in platforms_data:
        try:
            platform_id = platform_data.get('platform_id')
            if not platform_id:
                errors.append('platform_id is required for each platform')
                continue

            # Verify platform exists
            platform = SocialPlatform.query.get(platform_id)
            if not platform:
                errors.append(f'Platform with id {platform_id} not found')
                continue

            # Check if post-platform combination already exists
            existing = PostPlatform.query.filter_by(
                post_id=post_id, 
                platform_id=platform_id
            ).first()
            
            if existing:
                errors.append(f'Post already connected to platform {platform.name}')
                continue

            # Create post platform
            post_platform = PostPlatform(
                post_id=post_id,
                platform_id=platform_id,
                platform_caption=platform_data.get('platform_caption', post.caption),
                media_urls=platform_data.get('media_urls'),
                status='pending'
            )

            db.session.add(post_platform)
            created_platforms.append(post_platform)

        except Exception as e:
            errors.append(f'Error creating platform connection: {str(e)}')

    if errors:
        db.session.rollback()
        return jsonify({'error': 'Failed to create some platform connections', 'details': errors}), 400

    try:
        db.session.commit()
        return jsonify({
            'message': f'Successfully attached {len(created_platforms)} platforms',
            'post_platforms': [pp.to_dict() for pp in created_platforms]
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save platform connections'}), 500

#! Get Single Post Platform ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms/<int:platform_id>', methods=['GET'])
@login_required
def get_post_platform(post_id, platform_id):
    """
    GET /api/posts/:post_id/platforms/:platform_id – fetch one row
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_platform = PostPlatform.query.filter_by(
        post_id=post_id, 
        platform_id=platform_id
    ).first()
    
    if not post_platform:
        return jsonify({'error': 'Post-platform connection not found'}), 404

    return jsonify({'post_platform': post_platform.to_dict()})

#! Update Post Platform ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms/<int:platform_id>', methods=['PATCH'])
@login_required
def update_post_platform(post_id, platform_id):
    """
    PATCH /api/posts/:post_id/platforms/:platform_id – update platform_caption, media_urls, or status
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_platform = PostPlatform.query.filter_by(
        post_id=post_id, 
        platform_id=platform_id
    ).first()
    
    if not post_platform:
        return jsonify({'error': 'Post-platform connection not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update fields if provided
    if 'platform_caption' in data:
        post_platform.platform_caption = data['platform_caption']
    
    if 'media_urls' in data:
        post_platform.media_urls = data['media_urls']
    
    if 'status' in data:
        valid_statuses = ['pending', 'queued', 'publishing', 'published', 'failed', 'skipped']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        post_platform.status = data['status']
        
        # Set published_at if status becomes published
        if data['status'] == 'published' and not post_platform.published_at:
            post_platform.published_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({
            'message': 'Post platform updated successfully',
            'post_platform': post_platform.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update post platform'}), 500

#! Delete Post Platform ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms/<int:platform_id>', methods=['DELETE'])
@login_required
def delete_post_platform(post_id, platform_id):
    """
    DELETE /api/posts/:post_id/platforms/:platform_id – detach platform
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_platform = PostPlatform.query.filter_by(
        post_id=post_id, 
        platform_id=platform_id
    ).first()
    
    if not post_platform:
        return jsonify({'error': 'Post-platform connection not found'}), 404

    try:
        db.session.delete(post_platform)
        db.session.commit()
        return jsonify({'message': 'Platform detached successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to detach platform'}), 500

#! Queue Post Platform ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms/<int:platform_id>/queue', methods=['POST'])
@login_required
def queue_post_platform(post_id, platform_id):
    """
    POST /api/posts/:post_id/platforms/:platform_id/queue – set status=queued
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_platform = PostPlatform.query.filter_by(
        post_id=post_id, 
        platform_id=platform_id
    ).first()
    
    if not post_platform:
        return jsonify({'error': 'Post-platform connection not found'}), 404

    # Only allow queuing if status is pending
    if post_platform.status != 'pending':
        return jsonify({'error': f'Cannot queue post with status: {post_platform.status}'}), 400

    post_platform.status = 'queued'

    try:
        db.session.commit()
        return jsonify({
            'message': 'Post queued for publishing',
            'post_platform': post_platform.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to queue post'}), 500

#! Retry Post Platform ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms/<int:platform_id>/retry', methods=['POST'])
@login_required
def retry_post_platform(post_id, platform_id):
    """
    POST /api/posts/:post_id/platforms/:platform_id/retry – retry failed
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_platform = PostPlatform.query.filter_by(
        post_id=post_id, 
        platform_id=platform_id
    ).first()
    
    if not post_platform:
        return jsonify({'error': 'Post-platform connection not found'}), 404

    # Only allow retry if status is failed
    if post_platform.status != 'failed':
        return jsonify({'error': f'Can only retry failed posts. Current status: {post_platform.status}'}), 400

    post_platform.status = 'pending'

    try:
        db.session.commit()
        return jsonify({
            'message': 'Post marked for retry',
            'post_platform': post_platform.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to retry post'}), 500

#! Cancel Post Platform ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/posts/<int:post_id>/platforms/<int:platform_id>/cancel', methods=['POST'])
@login_required
def cancel_post_platform(post_id, platform_id):
    """
    POST /api/posts/:post_id/platforms/:platform_id/cancel – set status=skipped
    """
    # Verify post exists and belongs to current user
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_platform = PostPlatform.query.filter_by(
        post_id=post_id, 
        platform_id=platform_id
    ).first()
    
    if not post_platform:
        return jsonify({'error': 'Post-platform connection not found'}), 404

    # Don't allow canceling already published posts
    if post_platform.status == 'published':
        return jsonify({'error': 'Cannot cancel already published post'}), 400

    post_platform.status = 'skipped'

    try:
        db.session.commit()
        return jsonify({
            'message': 'Post cancelled successfully',
            'post_platform': post_platform.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel post'}), 500

#! Cross-Post View ///////////////////////////////////////////////////////////////////////////
@post_platforms_routes.route('/', methods=['GET'])
@login_required
def get_cross_post_view():
    """
    GET /api/post-platforms – cross-post view
    Filters: status, platform_id, published_from, published_to
    """
    # Get query parameters
    status = request.args.get('status')
    platform_id = request.args.get('platform_id')
    published_from = request.args.get('published_from')
    published_to = request.args.get('published_to')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Build query - only show posts from current user
    query = PostPlatform.query.join(Post).filter(Post.user_id == current_user.id)

    # Apply filters
    if status:
        valid_statuses = ['pending', 'queued', 'publishing', 'published', 'failed', 'skipped']
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        query = query.filter(PostPlatform.status == status)

    if platform_id:
        try:
            platform_id = int(platform_id)
            query = query.filter(PostPlatform.platform_id == platform_id)
        except ValueError:
            return jsonify({'error': 'platform_id must be a valid integer'}), 400

    if published_from:
        try:
            published_from_dt = datetime.fromisoformat(published_from.replace('Z', '+00:00'))
            query = query.filter(PostPlatform.published_at >= published_from_dt)
        except ValueError:
            return jsonify({'error': 'published_from must be in ISO format'}), 400

    if published_to:
        try:
            published_to_dt = datetime.fromisoformat(published_to.replace('Z', '+00:00'))
            query = query.filter(PostPlatform.published_at <= published_to_dt)
        except ValueError:
            return jsonify({'error': 'published_to must be in ISO format'}), 400

    # Pagination
    paginated = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

    return jsonify({
        'post_platforms': [pp.to_dict() for pp in paginated.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    })