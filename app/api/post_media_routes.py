#THIS IS ONLY A JOINING TABLE FOR POSTS AND MEDIA I DON'T THINK WE NEED THIS TABLE 

"""
post_media_routes.py (post_media)

GET /api/posts/:post_id/media – list media attached to a post (ordered by sort_order).

POST /api/posts/:post_id/media – attach one/many media_ids[] (optional sort_order).

PATCH /api/posts/:post_id/media/:media_id – update sort_order.

DELETE /api/posts/:post_id/media/:media_id – detach.

POST /api/posts/:post_id/media/reorder – bulk reorder [{"media_id","sort_order"}...].
"""