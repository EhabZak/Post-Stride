# app/api/admin_jobs_routes.py
from flask import Blueprint, request, jsonify, current_app
from rq.job import Job
from rq.registry import ScheduledJobRegistry
from app.extensions.queue import redis_conn, get_queue
from app.models import Post, PostPlatform  # adjust if needed
from rq_scheduler import Scheduler

admin_jobs_routes = Blueprint("admin_jobs", __name__, url_prefix="/api")

# -- internal helper -----------------------------------------------------------
def _get_redis_connection():
    """
    Return a live Redis connection.
    Prefer the explicitly-initialized redis_conn; otherwise, obtain it from the active RQ queue.
    Raises RuntimeError with a clear message if neither is available.
    """
    if redis_conn:
        return redis_conn
    q = get_queue() if 'get_queue' in globals() else None
    if q and getattr(q, "connection", None):
        return q.connection
    raise RuntimeError("Could not resolve a Redis connection. Make sure init_redis(...) was called "
                       "in app/__init__.py and that get_queue() returns a configured Queue.")

#! Inspect job /////////////////////////////////////////////////////////////////////////// ok
@admin_jobs_routes.route("/jobs/inspect", methods=["GET"])
def inspect_job():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    try:
        conn = _get_redis_connection()
        job = Job.fetch(job_id, connection=conn)
        return jsonify({
            "job_id": job.id,
            "status": job.get_status(),
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "origin": job.origin,
            "meta": job.meta or {},
        }), 200
    except Exception as e:
        current_app.logger.exception("[admin.jobs.inspect] error")
        # RQ throws KeyError for unknown jobs; connection errors raise RuntimeError/ConnectionError
        return jsonify({"error": str(e)}), 404

#! List scheduled jobs /////////////////////////////////////////////////////////////////////////// ok
@admin_jobs_routes.route("/jobs/scheduled", methods=["GET"])
def list_scheduled_jobs():
    try:
        q = get_queue()
        if not q:
            raise RuntimeError("Queue is not configured.")

        # ✅ This replaces reg = ScheduledJobRegistry(queue=q)
        reg = Scheduler(queue=q, connection=q.connection)

        jobs = reg.get_jobs()  # like reg.get_job_ids(), but returns Job objects
        job_list = [
            {"id": j.id, "func": j.func_name, "meta": j.meta or {}}
            for j in jobs
        ]

        return jsonify({"queue": q.name, "scheduled_jobs": job_list}), 200
    except Exception as e:
        current_app.logger.exception("[admin.jobs.scheduled] error")
        return jsonify({"error": str(e)}), 500

#! Get post status ///////////////////////////////////////////////////////////////////////////
@admin_jobs_routes.route("/posts/<int:post_id>/status", methods=["GET"])
def post_status(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    platforms = []
    for pp in PostPlatform.query.filter_by(post_id=post_id).all():
        # pp.platform is likely a relationship; serialize a simple string to avoid JSON errors
        platform_name = getattr(pp.platform, "name", None) or str(pp.platform)
        platforms.append({
            "platform": platform_name,
            "status": pp.status,
            "platform_post_id": pp.platform_post_id,
            "published_at": pp.published_at.isoformat() + "Z" if pp.published_at else None
        })

    return jsonify({
        "post_id": post.id,
        "status": post.status,
        "scheduled_time_utc": post.scheduled_time.isoformat() + "Z" if post.scheduled_time else None,
        "platforms": platforms
    }), 200
