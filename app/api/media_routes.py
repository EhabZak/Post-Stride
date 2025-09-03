#I DON'T KNOW IF WE NEED THIS

"""
media_routes.py (media)

GET /api/media – list; filters: media_type, from/to (created_at), post_id, q (name if stored).

POST /api/media – upload → S3 (save url, media_type).

GET /api/media/:id – fetch one (ownership).

DELETE /api/media/:id – delete (and detach from posts).

POST /api/media/bulk-delete – delete many by IDs.
"""