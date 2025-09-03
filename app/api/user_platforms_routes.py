"""
user_platforms_routes.py (user_platforms)

GET /api/user-platforms – list current user’s connections; filters: platform_id, expires_before, status=active|expired.

POST /api/user-platforms – connect/create (stores platform_user_id, tokens, expiry).

GET /api/user-platforms/:id – fetch one (ownership).

PATCH /api/user-platforms/:id – rotate tokens/update info.

DELETE /api/user-platforms/:id – disconnect.

POST /api/user-platforms/:id/refresh-token – force refresh.

GET /api/user-platforms/check-duplicates – pre-create uniqueness check.


"""