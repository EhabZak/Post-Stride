#I DON'T KNOW IF WE NEED THIS

"""
media_routes.py (media)

GET /api/media – list; filters: media_type, from/to (created_at), post_id, q (name if stored) of the user. ok

POST /api/media – to create / upload media- upload → S3 (save url, media_type). ok

GET /api/media/:id – fetch one media record by id (ownership). ok

DELETE /api/media/:id – delete a media record by id (and detach from posts). ok

POST /api/media/bulk-delete – delete many by IDs. ook
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Media, PostMedia
from datetime import datetime
import re

media_routes = Blueprint('media', __name__)

#! Parse ISO Datetime helper function //////////////////////////////////////////////////////////////
def parse_iso_datetime(datetime_str):
    """
    Parse ISO datetime string, handling 'Z' suffix and converting to timezone-naive UTC
    """
    if not datetime_str:
        return None
    
    # Replace 'Z' with '+00:00' for proper ISO parsing
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1] + '+00:00'
    
    try:
        dt = datetime.fromisoformat(datetime_str)
        # Convert to timezone-naive UTC
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except ValueError:
        return None

#! List Media ///////////////////////////////////////////////////////////////////////////
@media_routes.route('/', methods=['GET'])
@login_required
def get_media():
    """
    GET /api/media – list media with filters
    Filters: media_type, from/to (created_at), post_id, q (search)
    """
    # Get query parameters /// these below are here if you want to filter from the url that you are sending like 
    # http://localhost:5000/api/media?media_type=image&from=2025-01-01&to=2025-01-01&post_id=1&q=test
    media_type = request.args.get('media_type')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    post_id = request.args.get('post_id')
    q = request.args.get('q')  # search query
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    print("*************",request.args.to_dict(), "*************")

    # Build query - only show media from current user
    query = Media.query.filter_by(user_id=current_user.id)

    # Apply filters
    if media_type:
        valid_types = ['image', 'video', 'gif', 'audio', 'document']
        if media_type not in valid_types:
            return jsonify({'error': f'Invalid media_type. Must be one of: {", ".join(valid_types)}'}), 400
        query = query.filter(Media.media_type == media_type)

    if from_date:
        from_dt = parse_iso_datetime(from_date)
        if not from_dt:
            return jsonify({'error': 'Invalid from date format. Use ISO format.'}), 400
        query = query.filter(Media.created_at >= from_dt)

    if to_date:
        to_dt = parse_iso_datetime(to_date)
        if not to_dt:
            return jsonify({'error': 'Invalid to date format. Use ISO format.'}), 400
        query = query.filter(Media.created_at <= to_dt)

    if post_id:
        try:
            post_id = int(post_id)
            # Join with PostMedia to filter by post_id
            query = query.join(PostMedia).filter(PostMedia.post_id == post_id)
        except ValueError:
            return jsonify({'error': 'post_id must be a valid integer'}), 400

    if q:
        # Search in URL (since we don't have a name field, we'll search in URL)
        query = query.filter(Media.url.contains(q))

    # Order by created_at descending
    query = query.order_by(Media.created_at.desc())

    # Pagination
    paginated = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

    return jsonify({
        'media': [media.to_dict() for media in paginated.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    })

#! Upload Media ///////////////////////////////////////////////////////////////////////////
@media_routes.route('/', methods=['POST'])
@login_required
def upload_media():
    """
    POST /api/media – upload media to S3 and save metadata
    Note: This is a placeholder implementation. In production, you'd integrate with S3.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate required fields
    url = data.get('url')
    media_type = data.get('media_type')

    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not media_type:
        return jsonify({'error': 'media_type is required'}), 400

    # Validate media_type
    valid_types = ['image', 'video', 'gif', 'audio', 'document']
    if media_type not in valid_types:
        return jsonify({'error': f'Invalid media_type. Must be one of: {", ".join(valid_types)}'}), 400

    # Validate URL format
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return jsonify({'error': 'Invalid URL format'}), 400

    try:
        # Create media record
        media = Media(
            user_id=current_user.id,
            media_type=media_type,
            url=url
        )

        db.session.add(media)
        db.session.commit()

        return jsonify({
            'message': 'Media uploaded successfully',
            'media': media.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save media'}), 500

#! Get Single Media ///////////////////////////////////////////////////////////////////////////
@media_routes.route('/<int:media_id>', methods=['GET'])
@login_required
def get_media_by_id(media_id):
    """
    GET /api/media/:id – fetch single media with ownership check
    """
    media = Media.query.filter_by(id=media_id, user_id=current_user.id).first()
    
    if not media:
        return jsonify({'error': 'Media not found'}), 404

    return jsonify({'media': media.to_dict()})

#! Delete Media ///////////////////////////////////////////////////////////////////////////
@media_routes.route('/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    """
    DELETE /api/media/:id – delete media and detach from posts
    """
    media = Media.query.filter_by(id=media_id, user_id=current_user.id).first()
    
    if not media:
        return jsonify({'error': 'Media not found'}), 404

    try:
        # The cascade='all, delete-orphan' in the Media model's post_media relationship
        # will automatically handle detaching from posts when we delete the media
        db.session.delete(media)
        db.session.commit()

        return jsonify({'message': 'Media deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete media'}), 500

#! Bulk Delete Media ///////////////////////////////////////////////////////////////////////////
@media_routes.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_media():
    """
    POST /api/media/bulk-delete – delete multiple media by IDs
    """
    data = request.get_json()
    if not data or 'media_ids' not in data:
        return jsonify({'error': 'media_ids array is required'}), 400

    media_ids = data['media_ids']
    if not isinstance(media_ids, list):
        return jsonify({'error': 'media_ids must be an array'}), 400

    if not media_ids:
        return jsonify({'error': 'media_ids cannot be empty'}), 400

    # Validate all IDs are integers
    try:
        media_ids = [int(id) for id in media_ids]
    except (ValueError, TypeError):
        return jsonify({'error': 'All media_ids must be valid integers'}), 400

    # Find media that belong to current user
    media_to_delete = Media.query.filter(
        Media.id.in_(media_ids),
        Media.user_id == current_user.id
    ).all()

    if not media_to_delete:
        return jsonify({'error': 'No media found with the provided IDs'}), 404

    deleted_count = len(media_to_delete)
    deleted_ids = [media.id for media in media_to_delete]

    try:
        # Delete all found media (cascade will handle post_media relationships)
        for media in media_to_delete:
            db.session.delete(media)
        
        db.session.commit()

        return jsonify({
            'message': f'Successfully deleted {deleted_count} media items',
            'deleted_ids': deleted_ids,
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete media'}), 500