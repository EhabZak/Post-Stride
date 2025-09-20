from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Post, PostPlatform, PostMedia, Media, SocialPlatform
from datetime import datetime, timezone
import re

posts_routes = Blueprint('posts', __name__)

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

#! Get all posts ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('', methods=['GET'])
@login_required
def get_posts():
    """
    GET /api/posts – list posts with filters and sorting
    """

    # return jsonify({'message': 'Hello, World!'}), 200
    try:
        # Get query parameters /////////////////////////////////////
        status = request.args.get('status')
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        platform_id = request.args.get('platform_id')
        has_media = request.args.get('has_media')
        q = request.args.get('q')  # caption search
        sort_by = request.args.get('sort', 'created_at')  # default sort by created_at
        
        # Start with base query for current user /////////////////////////////////////
        query = Post.query.filter_by(user_id=current_user.id)
        
        # Apply filters /////////////////////////////////////
        if status:
            query = query.filter(Post.status == status)
        
        if from_date:
            try:
                from_datetime = parse_iso_datetime(from_date)
                query = query.filter(Post.scheduled_time >= from_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid from_date format. Use ISO format.'}), 400
        
        if to_date:
            try:
                to_datetime = parse_iso_datetime(to_date)
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
        
        # Apply sorting /////////////////////////////////////
        if sort_by == 'scheduled_time':
            query = query.order_by(Post.scheduled_time.asc())
        elif sort_by == 'created_at':
            query = query.order_by(Post.created_at.desc())
        elif sort_by == 'status':
            query = query.order_by(Post.status.asc())
        else:
            return jsonify({'error': 'Invalid sort parameter. Use: scheduled_time, created_at, or status.'}), 400
        
        # Execute query /////////////////////////////////////
        posts = query.all()
        
        # Convert to dictionary format /////////////////////////////////////
        posts_data = []
        for post in posts:
            post_data = post.to_dict()
            
            # Add platform information /////////////////////////////////////
            post_data['platforms'] = []
            for post_platform in post.post_platforms:
                platform_data = {
                    'platform_id': post_platform.platform_id,
                    'platform_name': post_platform.platform.name,
                    'status': post_platform.status,
                    'published_at': post_platform.published_at.isoformat() if post_platform.published_at else None
                }
                post_data['platforms'].append(platform_data)
            
            # Add media information /////////////////////////////////////
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
        
        # Validate required fields /////////////////////////////////////
        if not data or 'caption' not in data:
            return jsonify({'error': 'Caption is required'}), 400
        
        caption = data['caption']
        scheduled_time = data.get('scheduled_time')
        status = data.get('status', 'draft')  # default to draft
        
        # Validate status /////////////////////////////////////
        valid_statuses = ['draft', 'scheduled', 'publishing', 'published', 'partially_published', 'failed', 'canceled']
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Parse scheduled_time if provided /////////////////////////////////////
        if scheduled_time:
            try:
                scheduled_time = parse_iso_datetime(scheduled_time)
            except ValueError:
                return jsonify({'error': 'Invalid scheduled_time format. Use ISO format.'}), 400
        
        # Create new post /////////////////////////////////////
        new_post = Post(
            user_id=current_user.id,
            caption=caption,
            scheduled_time=scheduled_time,
            status=status
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        # Return created post /////////////////////////////////////
        post_data = new_post.to_dict()
        return jsonify({'post': post_data}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Get a post by id ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    """
    GET /api/posts/:id – fetch one post with media and platform details
    """
    try:
        # Find post belonging to current user /////////////////////////////////////
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Get post data /////////////////////////////////////
        post_data = post.to_dict()
        
        # Add detailed platform information /////////////////////////////////////
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
        
        # Add detailed media information /////////////////////////////////////
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

#! Update a post ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('/<int:post_id>', methods=['PATCH'])
@login_required
def update_post(post_id):
    """
    PATCH /api/posts/:id – update caption/scheduled_time/status
    """
    try:
        # Find post belonging to current user
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update caption if provided
        if 'caption' in data:
            post.caption = data['caption']
        
        # Update scheduled_time if provided
        if 'scheduled_time' in data:
            if data['scheduled_time'] is None:
                post.scheduled_time = None
            else:
                try:
                    post.scheduled_time = parse_iso_datetime(data['scheduled_time'])
                except ValueError:
                    return jsonify({'error': 'Invalid scheduled_time format. Use ISO format.'}), 400
        
        # Update status if provided
        if 'status' in data:
            valid_statuses = ['draft', 'scheduled', 'publishing', 'published', 'partially_published', 'failed', 'canceled']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            post.status = data['status']
        
        # Update the updated_at timestamp
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'post': post.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Delete a post ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """
    DELETE /api/posts/:id – delete post (cascade post_platforms & post_media)
    """
    try:
        # Find post belonging to current user
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Delete the post (cascade will handle related records)
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Schedule a post ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('/<int:post_id>/schedule', methods=['POST'])
@login_required
def schedule_post(post_id):
    """
    POST /api/posts/:id/schedule – set scheduled_time, status=scheduled
    """
    try:
        # Find post belonging to current user
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        data = request.get_json()
        if not data or 'scheduled_time' not in data:
            return jsonify({'error': 'scheduled_time is required'}), 400
        
        # Parse and validate scheduled_time
        try:
            scheduled_time = parse_iso_datetime(data['scheduled_time'])
        except ValueError:
            return jsonify({'error': 'Invalid scheduled_time format. Use ISO format.'}), 400
        
        # Check if scheduled time is in the future
        if scheduled_time <= datetime.utcnow():
            return jsonify({'error': 'Scheduled time must be in the future'}), 400
        
        # Update post
        post.scheduled_time = scheduled_time
        post.status = 'scheduled'
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'post': post.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Cancel a post ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('/<int:post_id>/cancel', methods=['POST'])
@login_required
def cancel_post(post_id):
    """
    POST /api/posts/:id/cancel – set status=canceled
    """
    try:
        # Find post belonging to current user
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Update status to canceled
        post.status = 'canceled'
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'post': post.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#! Duplicate a post ///////////////////////////////////////////////////////////////////////////

@posts_routes.route('/<int:post_id>/duplicate', methods=['POST'])
@login_required
def duplicate_post(post_id):
    """
    POST /api/posts/:id/duplicate – clone post (clear per-platform ids/statuses)
    """
    try:
        # Find post belonging to current user
        original_post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        print(original_post)
        
        if not original_post:
            return jsonify({'error': 'Post not found'}), 404
        
        # Create new post with same caption but draft status
        new_post = Post(
            user_id=current_user.id,
            caption=original_post.caption,
            scheduled_time=None,  # Clear scheduled time
            status='draft'  # Reset to draft status
        )
        
        db.session.add(new_post)
        db.session.flush()  # Get the new post ID
        
        # Duplicate post_platforms (but clear platform-specific data)
        for original_platform in original_post.post_platforms:
            new_platform = PostPlatform(
                post_id=new_post.id,
                platform_id=original_platform.platform_id,
                platform_caption=original_platform.platform_caption,
                media_urls=original_platform.media_urls,
                platform_post_id=None,  # Clear platform post ID
                status='draft',  # Reset status
                published_at=None  # Clear published time
            )
            db.session.add(new_platform)
        
        # Duplicate post_media
        for original_media in original_post.post_media:
            new_media = PostMedia(
                post_id=new_post.id,
                media_id=original_media.media_id,
                sort_order=original_media.sort_order
            )
            db.session.add(new_media)
        
        db.session.commit()
        
        # Return the duplicated post with full details
        post_data = new_post.to_dict()
        
        # Add platform information
        post_data['platforms'] = []
        for post_platform in new_post.post_platforms:
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
        
        # Add media information
        post_data['media'] = []
        for post_media in new_post.post_media:
            media_data = {
                'media_id': post_media.media_id,
                'media_type': post_media.media.media_type,
                'url': post_media.media.url,
                'sort_order': post_media.sort_order,
                'added_at': post_media.added_at.isoformat()
            }
            post_data['media'].append(media_data)
        
        return jsonify({'post': post_data}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

"""
posts_routes.py (posts) 

GET /api/posts – list; filters: status, from/to (scheduled_time), platform_id, has_media, q (caption); sort by scheduled_time|created_at|status. ok

POST /api/posts – create (caption, optional scheduled_time, status=draft|scheduled). ok

GET /api/posts/:id – fetch one (may include media + per-platform). ok

PATCH /api/posts/:id – update caption/scheduled_time/status. ok

DELETE /api/posts/:id – delete (cascade post_platforms & post_media). ok

POST /api/posts/:id/schedule – set scheduled_time, status=scheduled.

POST /api/posts/:id/cancel – set status=canceled. ok

POST /api/posts/:id/duplicate – clone post (clear per-platform ids/statuses). ok

"""