from datetime import datetime
from flask import current_app
# from app import app as flask_app          # <-- use the global app you already create
from app.models import db, Post, PostPlatform, SocialPlatform
from app.extensions.queue import get_queue  # your RQ queue getter
from app.utils.timezone_helpers import to_utc_naive  # Ensure UTC consistency
from rq import Retry, get_current_job
from app.scheduler import mark_scheduled_job_status  



# =============================================================================
# TIMEZONE CONVENTION
# =============================================================================
# All datetime operations in this file use datetime.utcnow() to maintain UTC consistency.
# Database stores naive UTC datetimes. API layer handles timezone conversion for users.

# =============================================================================
# Public API (called by your routes / scheduler)
# =============================================================================

#! publish_post older version does not update scheduled_jobs status  ///////////////////////////////////////////////////////////////////////////    

# def publish_post(post_id: int):
#     """
#     If job.meta contains platform_id -> publish that ONE platform inline (no extra enqueue).
#     Otherwise (no platform_id) -> orchestrate by enqueuing each platform row.
#     Also mirrors status to scheduled_jobs via scheduled_job_id in job.meta.
#     """
#     job = get_current_job()
#     meta = (job.meta or {}) if job else {}
#     scheduled_job_id = meta.get("scheduled_job_id")
#     target_platform_id = meta.get("platform_id")

#     def _sj(status: str, **kw):
#         if scheduled_job_id:
#             try:
#                 mark_scheduled_job_status(scheduled_job_id, status, **kw)
#             except Exception:
#                 pass

#     current_app.logger.info(f"[tasks.publish_post] start post_id={post_id} platform={target_platform_id}")
#     _sj("started")

#     post = Post.query.get(post_id)
#     if not post:
#         current_app.logger.warning(f"[tasks.publish_post] post {post_id} not found")
#         _sj("failed", error_message=f"Post {post_id} not found")
#         return

#     if getattr(post, "status", None) in ("published", "canceled"):
#         current_app.logger.info(f"[tasks.publish_post] post {post_id} status={post.status}, skip")
#         _sj("finished")
#         return

#     # ------- SINGLE-PLATFORM PATH (scheduled per-platform job) -------
#     if target_platform_id is not None:
#         pp = PostPlatform.query.filter_by(post_id=post.id, platform_id=target_platform_id).first()
#         if not pp:
#             current_app.logger.warning(f"[tasks.publish_post] no PostPlatform for post={post.id} platform={target_platform_id}")
#             _sj("failed", error_message="PostPlatform row not found")
#             return

#         # skip if already done
#         if pp.status in ("publishing", "published", "skipped"):
#             current_app.logger.info(f"[tasks.publish_post] already handled pp_id={pp.id} status={pp.status}")
#             _sj("finished")
#             return

#         # run inline for this platform (no extra enqueue)
#         try:
#             pp.status = "publishing"
#             db.session.commit()
#             publish_post_platform(pp.id)  # <-- synchronous publish for the targeted platform
#             _recompute_parent_post_status(post.id)
#             _sj("finished")
#             current_app.logger.info(f"[tasks.publish_post] finished inline platform publish pp_id={pp.id}")
#         except Exception as e:
#             current_app.logger.exception("single-platform publish failed")
#             _sj("failed", error_message=str(e))
#         return

#     # ------- ORCHESTRATOR PATH (no specific platform in meta) -------
#     pps = PostPlatform.query.filter_by(post_id=post.id).all()
#     if not pps:
#         current_app.logger.info(f"[tasks.publish_post] post {post_id} has no platforms; marking published")
#         post.status = "published"
#         if hasattr(post, "published_at"):
#             post.published_at = datetime.utcnow()
#         db.session.commit()
#         _sj("finished")
#         return

#     q = get_queue()
#     enqueued_any = False
#     for pp in pps:
#         if pp.status in ("queued", "publishing", "published", "skipped"):
#             current_app.logger.info(f"[tasks.publish_post] skip pp_id={pp.id} status={pp.status}")
#             continue

#         pp.status = "queued"
#         db.session.commit()

#         # enqueue per-platform worker
#         q.enqueue(publish_post_platform, pp.id, retry=_retry_policy())
#         enqueued_any = True
#         current_app.logger.info(f"[tasks.publish_post] enqueued pp_id={pp.id}")

#     _recompute_parent_post_status(post.id)

#     # Orchestrator job has done its work; mark finished even if nothing new was enqueued
#     _sj("finished")
#     if not enqueued_any:
#         current_app.logger.info(f"[tasks.publish_post] nothing enqueued for post {post_id}")
        
#///////2 working correctly ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def publish_post(post_id: int):
    """
    If job.meta contains platform_id -> publish that ONE platform inline (no extra enqueue).
    Otherwise (no platform_id) -> orchestrate by enqueuing each platform row.
    Mirrors status to scheduled_jobs via scheduled_job_id in job.meta using YOUR states:
      scheduled -> pending -> (published | failed | canceled)
    """
    job = get_current_job()
    meta = (job.meta or {}) if job else {}
    scheduled_job_id = meta.get("scheduled_job_id")
    target_platform_id = meta.get("platform_id")

    def _sj(status: str, **kw):
        if scheduled_job_id:
            try:
                # your helper should set timestamps (started_at/finished_at) as needed
                mark_scheduled_job_status(scheduled_job_id, status, **kw)
            except Exception:
                pass

    current_app.logger.info(f"[tasks.publish_post] start post_id={post_id} platform={target_platform_id}")
    _sj("pending")  # worker picked it up -> pending

    post = Post.query.get(post_id)
    if not post:
        current_app.logger.warning(f"[tasks.publish_post] post {post_id} not found")
        _sj("failed", error_message=f"Post {post_id} not found")
        return

    # If the whole post is already terminal, reflect that in the job row
    if getattr(post, "status", None) in ("published", "canceled"):
        current_app.logger.info(f"[tasks.publish_post] post {post_id} status={post.status}, skip")
        _sj("published" if post.status == "published" else "canceled")
        return

    # ------- SINGLE-PLATFORM PATH (scheduled per-platform job) -------
    if target_platform_id is not None:
        pp = PostPlatform.query.filter_by(post_id=post.id, platform_id=target_platform_id).first()
        if not pp:
            current_app.logger.warning(f"[tasks.publish_post] no PostPlatform for post={post.id} platform={target_platform_id}")
            _sj("failed", error_message="PostPlatform row not found")
            return

        # idempotent handling: map existing pp.status to scheduled_jobs status
        if pp.status in ("published",):
            current_app.logger.info(f"[tasks.publish_post] already published pp_id={pp.id}")
            _sj("published")
            return
        if pp.status in ("skipped", "canceled"):
            current_app.logger.info(f"[tasks.publish_post] already canceled/skipped pp_id={pp.id}")
            _sj("canceled")
            return
        if pp.status in ("publishing", "queued"):
            current_app.logger.info(f"[tasks.publish_post] already in progress pp_id={pp.id} status={pp.status}")
            # stay as pending for the job row; do nothing further
            _sj("pending")
            return

        # run inline for this platform (no extra enqueue)
        try:
            pp.status = "publishing"
            db.session.commit()

            publish_post_platform(pp.id)  # <-- synchronous publish for the targeted platform

            # After successful publish_post_platform, mark parent & job
            _recompute_parent_post_status(post.id)
            _sj("published")
            current_app.logger.info(f"[tasks.publish_post] finished inline platform publish pp_id={pp.id}")
        except Exception as e:
            current_app.logger.exception("single-platform publish failed")
            _sj("failed", error_message=str(e))
        return

    # ------- ORCHESTRATOR PATH (no specific platform in meta) -------
    pps = PostPlatform.query.filter_by(post_id=post.id).all()
    if not pps:
        current_app.logger.info(f"[tasks.publish_post] post {post_id} has no platforms; marking published")
        post.status = "published"
        if hasattr(post, "published_at"):
            post.published_at = datetime.utcnow()
        db.session.commit()
        _sj("published")
        return

    q = get_queue()
    enqueued_any = False
    for pp in pps:
        # Skip anything already handled/underway
        if pp.status in ("queued", "publishing", "published", "skipped", "canceled"):
            current_app.logger.info(f"[tasks.publish_post] skip pp_id={pp.id} status={pp.status}")
            continue

        pp.status = "queued"
        db.session.commit()

        # enqueue per-platform worker
        q.enqueue(publish_post_platform, pp.id, retry=_retry_policy())
        enqueued_any = True
        current_app.logger.info(f"[tasks.publish_post] enqueued pp_id={pp.id}")

    _recompute_parent_post_status(post.id)

    # Orchestrator has done its job. For the orchestrator's scheduled_job row:
    # - If it didn't enqueue anything new, we can mark as 'published' to indicate orchestration completed.
    #   (Alternatively, leave as 'pending' until children finish, but simpler is to close it out here.)
    _sj("published")
    if not enqueued_any:
        current_app.logger.info(f"[tasks.publish_post] nothing enqueued for post {post_id}")




# =============================================================================
# Worker job (one job per post_platform)
# =============================================================================

#! publish_post_platform /////////////////////////////////////////////////////////////////////////// 
def publish_post_platform(pp_id: int):
    """
    RQ job: publish a single post_platform row.
    Flow (mock):
      queued -> publishing -> published (or failed)

    For production → you'll replace the MOCK section with actual API calls to each platform.
    """
    pp = PostPlatform.query.get(pp_id)
    if not pp:
        current_app.logger.warning(f"[tasks.publish_pp] post_platform {pp_id} not found")
        return

    #! Idempotency guard
    # Prevents duplicate publish attempts for the same row.
    if pp.status in ("publishing", "published", "skipped"):
        current_app.logger.info(f"[tasks.publish_pp] skip pp_id={pp_id} status={pp.status}")
        return

    post = Post.query.get(pp.post_id)
    if not post:
        current_app.logger.warning(f"[tasks.publish_pp] parent post {pp.post_id} missing; marking failed")
        pp.status = "failed"
        db.session.commit()
        return

    platform = SocialPlatform.query.get(pp.platform_id)
    platform_name = (platform.name if platform and platform.name else "").strip().lower()

    # Move to publishing
    pp.status = "publishing"
    db.session.commit()

    try:
        '''
        ---------------------------------------------------------------------
        MOCK PUBLISH (safe for development)
        ---------------------------------------------------------------------

        This clarifies that everything below is a mock.
        This "example" section is only there so you can test the flow end-to-end 
        (schedule → enqueue → worker → database update) without yet writing 
        the real integrations for LinkedIn, X, Instagram, etc.

        For production → you’ll replace this part with actual API calls to each platform.
        '''
        # 1- Sets per-platform status → "published",
        # 2- Stores a fake platform_post_id (in real life, you’d save the ID returned by the platform API),
        # 3- Stamps published_at in UTC.

        pp.platform_post_id = f"mock-{pp.id}"
        pp.published_at = datetime.utcnow()
        pp.status = "published"
        db.session.commit()

        # 5. Updates statuses to "published"
        #! Set the aggregate post status 
        # Marks the overall post as published once all per-platform rows were “handled”.
        _recompute_parent_post_status(post.id)

        current_app.logger.info(f"[tasks.publish_pp] published OK pp_id={pp_id}")
        return {"ok": True, "pp_id": pp_id, "status": pp.status}

    except Exception as e:
        current_app.logger.exception(f"[tasks.publish_pp] publish failed pp_id={pp_id}: {e}")
        pp.status = "failed"
        db.session.commit()
        _recompute_parent_post_status(post.id)
        return {"ok": False, "pp_id": pp_id, "error": str(e)}

# =============================================================================
# Helpers
# =============================================================================

def _retry_policy():
    return Retry(max=3, interval=[60, 300, 900])


def _recompute_parent_post_status(post_id: int):
    """
    Aggregate per-platform statuses into the parent post.status.
    """
    pps = PostPlatform.query.filter_by(post_id=post_id).all()
    if not pps:
        return

    statuses = {p.status for p in pps}
    post = Post.query.get(post_id)
    if not post:
        return

    # Compute aggregate
    if "publishing" in statuses or "queued" in statuses:
        post.status = "publishing"
    elif statuses == {"published"}:
        post.status = "published"
        if hasattr(post, "published_at") and not getattr(post, "published_at", None):
            post.published_at = datetime.utcnow()
    elif "published" in statuses and ("failed" in statuses or "skipped" in statuses):
        # Some succeeded, some failed/
        
        post.status = "partially_published"
        if hasattr(post, "published_at") and not getattr(post, "published_at", None):
            post.published_at = datetime.utcnow()
    elif statuses == {"failed"}:
        post.status = "failed"
    else:
        # leave as-is (draft/scheduled/etc.)
        pass

    db.session.commit()


# =============================================================================
# Simple test utility (unchanged)
# =============================================================================

#! this is only a function to test if the worker is working or not in the beggining of the project
#! you don't need it or use it in your code  
def echo(msg: str):
    current_app.logger.info(f"[echo] {msg}")
    return msg
