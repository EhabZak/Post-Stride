"""
posts_routes.py (posts)

GET /api/posts – list; filters: status, from/to (scheduled_time), platform_id, has_media, q (caption); sort by scheduled_time|created_at|status.

POST /api/posts – create (caption, optional scheduled_time, status=draft|scheduled).

GET /api/posts/:id – fetch one (may include media + per-platform).

PATCH /api/posts/:id – update caption/scheduled_time/status.

DELETE /api/posts/:id – delete (cascade post_platforms & post_media).

POST /api/posts/:id/schedule – set scheduled_time, status=scheduled.

POST /api/posts/:id/cancel – set status=canceled.

POST /api/posts/:id/duplicate – clone post (clear per-platform ids/statuses).

"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Post, PostPlatform, PostMedia, Media, SocialPlatform
from datetime import datetime

posts_routes = Blueprint('posts', __name__)


@posts_routes.route('', methods=['GET'])
@login_required
def get_posts():
    """
    GET /api/posts – list posts with filters and sorting
    """

    # return jsonify({'message': 'Hello, World!'}), 200
    try:
        # Get query parameters
        status = request.args.get('status')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        platform_id = request.args.get('platform_id')
        has_media = request.args.get('has_media')
        q = request.args.get('q')  # caption search
        sort_by = request.args.get('sort', 'created_at')  # default sort by created_at
        
        # Start with base query for current user
        query = Post.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Post.status == status)
        
        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date)
                query = query.filter(Post.scheduled_time >= from_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid from_date format. Use ISO format.'}), 400
        
        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date)
                query = query.filter(Post.scheduled_time <= to_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid to_date format. Use ISO format.'}), 400
        
        if platform_id:
            try:
                platform_id = int(platform_id)
                query = query.join(PostPlatform).filter(PostPlatform.platform_id == platform_id)
            except ValueError:
                return jsonify({'error': 'Invalid platform_id. Must be an integer.'}), 400
        
        if has_media:
            if has_media.lower() == 'true':
                query = query.join(PostMedia)
            elif has_media.lower() == 'false':
                query = query.outerjoin(PostMedia).filter(PostMedia.post_id.is_(None))
        
        if q:
            query = query.filter(Post.caption.ilike(f'%{q}%'))
        
        # Apply sorting
        if sort_by == 'scheduled_time':
            query = query.order_by(Post.scheduled_time.asc())
        elif sort_by == 'created_at':
            query = query.order_by(Post.created_at.desc())
        elif sort_by == 'status':
            query = query.order_by(Post.status.asc())
        else:
            return jsonify({'error': 'Invalid sort parameter. Use: scheduled_time, created_at, or status.'}), 400
        
        # Execute query
        posts = query.all()
        
        # Convert to dictionary format
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            
            # Add platform information
            post_data['platforms'] = []
            for post_platform in post.post_platforms:
                platform_data = {
                    'platform_id': post_platform.platform_id,
                    'platform_name': post_platform.platform.name,
                    'status': post_platform.status,
                    'published_at': post_platform.published_at.isoformat() if post_platform.published_at else None
                }
                post_data['platforms'].append(platform_data)
            
            # Add media information
            post_data['media'] = []
            for post_media in post.post_media:
                media_data = {
                    'media_id': post_media.media_id,
                    'media_type': post_media.media.media_type,
                    'url': post_media.media.url,
                    'sort_order': post_media.sort_order
                }
                post_data['media'].append(media_data)
            
            posts_data.append(post_data)
        
        return jsonify({'posts': posts_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#! Create a post ///////////////////////////////////////////////////////////////////////////
@posts_routes.route('', methods=['POST'])
@login_required
def create_post():
    """
    POST /api/posts – create a new post
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'caption' not in data:
            return jsonify({'error': 'Caption is required'}), 400
        
        caption = data['caption']
        scheduled_time = data.get('scheduled_time')
        status = data.get('status', 'draft')  # default to draft
        
        # Validate status
        valid_statuses = ['draft', 'scheduled', 'publishing', 'published', 'partially_published', 'failed', 'canceled']
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Parse scheduled_time if provided
        if scheduled_time:
            try:
                scheduled_time = datetime.fromisoformat(scheduled_time)
            except ValueError:
                return jsonify({'error': 'Invalid scheduled_time format. Use ISO format.'}), 400
        
        # Create new post
        new_post = Post(
            user_id=current_user.id,
            caption=caption,
            scheduled_time=scheduled_time,
            status=status
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        # Return created post
        post_data = new_post.to_dict()
        return jsonify({'post': post_data}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@posts_routes.route('/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    """
    GET /api/posts/:id – fetch one post with media and platform details
    """
    try:
        # Find post belonging to current user
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Get post data
        post_data = post.to_dict()
        
        # Add detailed platform information
        post_data['platforms'] = []
        for post_platform in post.post_platforms:
            platform_data = {
                'id': post_platform.id,
                'platform_id': post_platform.platform_id,
                'platform_name': post_platform.platform.name,
                'platform_caption': post_platform.platform_caption,
                'media_urls': post_platform.media_urls,
                'platform_post_id': post_platform.platform_post_id,
                'status': post_platform.status,
                'published_at': post_platform.published_at.isoformat() if post_platform.published_at else None
            }
            post_data['platforms'].append(platform_data)
        
        # Add detailed media information
        post_data['media'] = []
        for post_media in post.post_media:
            media_data = {
                'media_id': post_media.media_id,
                'media_type': post_media.media.media_type,
                'url': post_media.media.url,
                'sort_order': post_media.sort_order,
                'added_at': post_media.added_at.isoformat()
            }
            post_data['media'].append(media_data)
        
        return jsonify({'post': post_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500