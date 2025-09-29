# app/api/admin_jobs_routes.py
from flask import Blueprint, request, jsonify
from rq.job import Job
from rq.registry import ScheduledJobRegistry
from app.extensions.queue import redis_conn, get_queue
from app.models import Post, PostPlatform  # adjust if needed

admin_jobs_routes = Blueprint("admin_jobs", __name__, url_prefix="/api")

#! Inspect job /////////////////////////////////////////////////////////////////////////// you need to check this one 
@admin_jobs_routes.route("/jobs/inspect", methods=["GET"])
def inspect_job():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return jsonify({
            "job_id": job.id,
            "status": job.get_status(),
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "origin": job.origin,
            "meta": job.meta or {},
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

#! List scheduled jobs /////////////////////////////////////////////////////////////////////////// this is ok i think need to check when there is a scheudled job 
@admin_jobs_routes.route("/jobs/scheduled", methods=["GET"])
def list_scheduled_jobs():
    q = get_queue()
    reg = ScheduledJobRegistry(queue=q)
    return jsonify({"scheduled_job_ids": reg.get_job_ids()}), 200

#! Get post status ///////////////////////////////////////////////////////////////////////////
@admin_jobs_routes.route("/posts/<int:post_id>/status", methods=["GET"])
def post_status(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    platforms = [{
        "platform": pp.platform,
        "status": pp.status,
        "platform_post_id": pp.platform_post_id,
        "published_at": pp.published_at.isoformat() + "Z" if pp.published_at else None
    } for pp in PostPlatform.query.filter_by(post_id=post_id).all()]

    return jsonify({
        "post_id": post.id,
        "status": post.status,
        "scheduled_time_utc": post.scheduled_time.isoformat() + "Z" if post.scheduled_time else None,
        "published_at": post.published_at.isoformat() + "Z" if post.published_at else None,
        "platforms": platforms
    }), 200
