"""
post_platforms_routes.py (post_platforms)

GET /api/posts/:post_id/platforms – list per-platform rows (filter status=pending|queued|publishing|published|failed|skipped).

POST /api/posts/:post_id/platforms – bulk attach platforms (create rows; allow per-platform caption/media).

GET /api/posts/:post_id/platforms/:platform_id – fetch one row.

PATCH /api/posts/:post_id/platforms/:platform_id – update platform_caption, media_urls, or status.

DELETE /api/posts/:post_id/platforms/:platform_id – detach platform.

POST /api/posts/:post_id/platforms/:platform_id/queue – set status=queued.

POST /api/posts/:post_id/platforms/:platform_id/retry – retry failed.

POST /api/posts/:post_id/platforms/:platform_id/cancel – set status=skipped.

(ops) GET /api/post-platforms – cross-post view; filters: status, platform_id, published_from/to.

"""