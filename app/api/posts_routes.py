from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Post, PostPlatform, PostMedia, Media, SocialPlatform
from datetime import datetime, timezone
import re
from rq import Retry
from app.extensions.queue import get_queue
from app.utils.timezone_helpers import (
    parse_iso_to_utc,
    format_dual_time,
    format_utc_with_z,
    to_utc_naive
)

# from app.scheduler import schedule_post_at

posts_routes = Blueprint('posts', __name__)

# Note: All old timezone helpers removed - now using app.utils.timezone_helpers

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
                from_datetime = parse_iso_to_utc(from_date, current_user.timezone)
                query = query.filter(Post.scheduled_time >= from_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid from_date format. Use ISO format.'}), 400
        
        if to_date:
            try:
                to_datetime = parse_iso_to_utc(to_date, current_user.timezone)
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
            
            # Add dual time format for scheduled_time (UTC + user local)
            if post.scheduled_time:
                post_data['scheduled_time_detail'] = format_dual_time(post.scheduled_time, current_user.timezone)
            
            # Add platform information /////////////////////////////////////
            post_data['platforms'] = []
            for post_platform in post.post_platforms:
                platform_data = {
                    'platform_id': post_platform.platform_id,
                    'platform_name': post_platform.platform.name,
                    'status': post_platform.status,
                    'published_at': format_utc_with_z(post_platform.published_at)
                }
                # Add dual time for published_at
                if post_platform.published_at:
                    platform_data['published_at_detail'] = format_dual_time(post_platform.published_at, current_user.timezone)
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
                scheduled_time = parse_iso_to_utc(scheduled_time, current_user.timezone)
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
        
        # Add dual time format for scheduled_time
        if post.scheduled_time:
            post_data['scheduled_time_detail'] = format_dual_time(post.scheduled_time, current_user.timezone)
        
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
                'published_at': format_utc_with_z(post_platform.published_at)
            }
            # Add dual time for published_at
            if post_platform.published_at:
                platform_data['published_at_detail'] = format_dual_time(post_platform.published_at, current_user.timezone)
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
                    post.scheduled_time = parse_iso_to_utc(data['scheduled_time'], current_user.timezone)
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
    POST /api/posts/:id/schedule
    body: {"scheduled_time": "2025-09-28T18:45:00Z"}

    - Parses ISO time (assumed UTC if "Z" provided or tz-aware).
    - Persists scheduled_time and sets post.status="scheduled".
    - Uses scheduler helper to enqueue a one-time job at the exact time.
    """
    from app.scheduler import schedule_post_at
    try:
        post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        data = request.get_json() or {}
        iso = data.get('scheduled_time')
        if not iso:
            return jsonify({'error': 'scheduled_time is required'}), 400

        # Parse & normalize to UTC-naive (uses user timezone for naive inputs)
        try:
            when_utc_naive = parse_iso_to_utc(iso, current_user.timezone)
        except Exception:
            return jsonify({'error': 'Invalid scheduled_time format. Use ISO 8601.'}), 400

        # Must be in the future (compare to UTC "now")
        if when_utc_naive <= datetime.utcnow():
            return jsonify({'error': 'Scheduled time must be in the future'}), 400

        # Persist schedule on the Post
        post.scheduled_time = when_utc_naive
        post.status = 'scheduled'
        post.updated_at = datetime.utcnow()
        db.session.commit()

    #     # Create a stable job id (handy for cancel/reschedule later)
    #     job_id = f"publish_post-{post.id}-{int(when_utc_naive.timestamp())}"

    #     # Enqueue the publish job exactly at that time via the scheduler helper
    #     # (This wraps Queue.enqueue_at with your standard retry + meta)
    #     job = schedule_post_at(
    #         post_id=post.id,
    #         when=when_utc_naive,
    #         job_id=job_id,
    #         meta={"post_id": post.id}
    #     )

    #     # Return attached platforms for convenience
    #     pps = PostPlatform.query.filter_by(post_id=post.id).all()
    #     platforms = [{"id": pp.platform_id, "name": pp.platform.name} for pp in pps]

    #     # Return dual time format (UTC + user local time)
    #     time_detail = format_dual_time(when_utc_naive, current_user.timezone)

    #     return jsonify({
    #         "message": "post scheduled",
    #         "post_id": post.id,
    #         "scheduled_time": format_utc_with_z(when_utc_naive),
    #         "scheduled_time_detail": time_detail,
    #         "rq_job_id": job.id,
    #         "platforms": platforms
    #     }), 200

    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({'error': str(e)}), 500
    # Get target platforms for this post
        pps = PostPlatform.query.filter_by(post_id=post.id).all()
        if not pps:
            return jsonify({'error': 'No platforms attached to this post'}), 400

        jobs = []
        for pp in pps:
            plat_id = pp.platform_id
            # Make job_id unique per platform
            job_id = f"publish_post-{post.id}-{plat_id}-{int(when_utc_naive.timestamp())}"
            job = schedule_post_at(
                post_id=post.id,
                when=when_utc_naive,
                platform_id=plat_id,                       # 🔹 key change
                job_id=job_id,
                meta={"post_id": post.id, "platform_id": plat_id}
            )
            jobs.append({
                "platform_id": plat_id,
                "rq_job_id": job.id
            })

        time_detail = format_dual_time(when_utc_naive, current_user.timezone)
        platforms = [{"id": pp.platform_id, "name": pp.platform.name} for pp in pps]

        return jsonify({
            "message": "post scheduled",
            "post_id": post.id,
            "scheduled_time": format_utc_with_z(when_utc_naive),
            "scheduled_time_detail": time_detail,
            "jobs": jobs,                                  # one entry per platform
            "platforms": platforms
        }), 200

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
                'published_at': format_utc_with_z(post_platform.published_at)
            }
            # Add dual time for published_at
            if post_platform.published_at:
                platform_data['published_at_detail'] = format_dual_time(post_platform.published_at, current_user.timezone)
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

#! Cancel the whole post’s future publishing  ///////////////////////////////////////////////////////////////////////////
@posts_routes.route("/<int:post_id>/cancel", methods=["POST"])
@login_required
def cancel_post_future(post_id):
    """
    Cancel all future publishing tasks for a post.
    Only the post owner can perform this action.
    """
    from app.models import Post
    from app.services.posts_cancel import cancel_entire_post_future

    # Verify post exists and belongs to current user
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    if post.user_id != current_user.id:
        return jsonify({'error': 'Forbidden: You do not own this post'}), 403

    # Proceed to cancel all future jobs for this post
    result = cancel_entire_post_future(post_id, as_status="canceled")
    return jsonify({"ok": True, **result}), 200

    
#! Reschedule a post ///////////////////////////////////////////////////////////////////////////

# POST /api/posts/:post_id/reschedule
# @posts_routes.route("/<int:post_id>/reschedule", methods=["POST"])
# @login_required
# def reschedule_post(post_id):
#     from dateutil.parser import isoparse
#     from app.models import Post, ScheduledJob, db
#     # auth: user owns the post
#     post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
#     if not post: return jsonify({"error":"Post not found"}), 404

#     data = request.get_json() or {}
#     new_when = isoparse(data["scheduled_time"])  # "2025-11-10T14:30:00Z"
#     platform_ids = set(data.get("platform_ids") or [])  # optional

#     # pick jobs to move: not terminal & (in selected platforms if provided)
#     q = ScheduledJob.query.filter(
#         ScheduledJob.post_id==post_id,
#         ~ScheduledJob.status.in_(("published","failed","canceled"))
#     )
#     if platform_ids:
#         q = q.filter(ScheduledJob.platform_id.in_(platform_ids))
#     jobs = q.all()
#     if not jobs: return jsonify({"ok": True, "rescheduled": 0}), 200

#     # reschedule each
#     from app.scheduler import reschedule  # your helper
#     count = 0
#     for sj in jobs:
#         reschedule(sj.id, new_when, created_by_user_id=current_user.id)
#         count += 1

#     return jsonify({"ok": True, "rescheduled": count}), 200
@posts_routes.route("/<int:post_id>/reschedule", methods=["POST"])
@login_required
def reschedule_post(post_id):
    """
    POST /api/posts/:post_id/reschedule
    Body: {
      "scheduled_time": "2025-11-10T14:30:00Z",
      "platform_ids": [1,3,5]   // optional; omit to reschedule all active
    }

    - Verifies ownership
    - Rejects past times (UTC)
    - Reschedules all non-terminal jobs for the given post/platforms
    - Recomputes posts.scheduled_time = earliest of remaining active jobs
    """
    from datetime import datetime
    from dateutil.parser import isoparse
    from app.models import db, Post
    from app.models.scheduled_job import ScheduledJob
    from app.scheduler import reschedule as reschedule_one  # your existing helper
    # If you have _to_utc_naive already available in this module, import it; otherwise inline:
    # from app.scheduler import _to_utc_naive

    # 1) Ownership check
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # 2) Parse input
    data = request.get_json() or {}
    iso = data.get("scheduled_time")
    if not iso:
        return jsonify({"error": "scheduled_time is required (ISO8601, e.g., 2025-11-10T14:30:00Z)"}), 400

    try:
        new_when = isoparse(iso)  # may be aware or naive
    except Exception:
        return jsonify({"error": "Invalid scheduled_time format"}), 400

    # Normalize to UTC-naive the same way your scheduler does
    when_utc = to_utc_naive(new_when)

    # 3) Reject past/now times (UTC)
    if when_utc <= datetime.utcnow():
        return jsonify({"error": "scheduled_time must be in the future (UTC)"}), 400

    platform_ids = set(data.get("platform_ids") or [])

    # 4) Pick non-terminal jobs to move
    active_statuses = ("scheduled", "pending")  # your active states
    q = ScheduledJob.query.filter(
        ScheduledJob.post_id == post_id,
        ScheduledJob.status.in_(active_statuses),
    )
    if platform_ids:
        q = q.filter(ScheduledJob.platform_id.in_(platform_ids))
    active_jobs = q.all()

    # If nothing to reschedule, you can choose to schedule fresh here or just return
    if not active_jobs:
        # No active jobs matched; leave as no-op
        return jsonify({"ok": True, "rescheduled": 0, "post_scheduled_time": post.scheduled_time}), 200

    # 5) Reschedule each selected job
    count = 0
    for sj in active_jobs:
        reschedule_one(sj.id, when_utc, created_by_user_id=current_user.id)
        count += 1

    # 6) Recompute the post's displayed scheduled_time (earliest active)
    next_times = (
        db.session.query(ScheduledJob.scheduled_for)
        .filter(
            ScheduledJob.post_id == post_id,
            ScheduledJob.status.in_(active_statuses),
        )
        .all()
    )
    post.scheduled_time = (min(t[0] for t in next_times) if next_times else None)
    db.session.commit()

    return jsonify({
        "ok": True,
        "rescheduled": count,
        "new_time": when_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "post_scheduled_time": (
            post.scheduled_time.strftime("%Y-%m-%dT%H:%M:%SZ") if post.scheduled_time else None
        ),
    }), 200
