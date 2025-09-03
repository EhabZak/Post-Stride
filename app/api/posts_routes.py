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