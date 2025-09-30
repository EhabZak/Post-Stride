# app/tasks.py
from datetime import datetime
from flask import current_app
from app import app as flask_app          # <-- use the global app you already create
from app.models import db, Post, PostPlatform, SocialPlatform
from app.extensions.queue import get_queue  # your RQ queue getter

# Create one global app for worker context
flask_app.app_context().push()


# =============================================================================
# Public API (called by your routes / scheduler)
# =============================================================================

#! publish_post ///////////////////////////////////////////////////////////////////////////    
def publish_post(post_id: int):
    """
    Orchestrator for a post: enqueue one job per post_platform row.
    Idempotent: skips if post not found or already final.
    """
    #! start log helps you trace worker logs. If a job crashes, you’ll know which post_id was running.
    current_app.logger.info(f"[tasks.publish_post] start post_id={post_id}")

    # 1. Finds the post by ID
    post = Post.query.get(post_id)
    if not post:
        current_app.logger.warning(f"[tasks.publish_post] post {post_id} not found")
        return

    # 2. Checks if already published/canceled (idempotent guard)
    #! Prevents duplicate publish attempts. If another job already finished (or the user canceled), do nothing. 
    # This saves you from race conditions, retries, or accidental double-clicks.
    if getattr(post, "status", None) in ("published", "canceled"):
        current_app.logger.info(f"[tasks.publish_post] post {post_id} status={post.status}, skip enqueue")
        return

    # 3. Gets all platform connections for the post
    pps = PostPlatform.query.filter_by(post_id=post.id).all()
    if not pps:
        # No platforms attached — consider the post published immediately (or keep as draft)
        current_app.logger.info(f"[tasks.publish_post] post {post_id} has no platforms; marking published")
        post.status = "published"
        # If your Post model has published_at, set it; otherwise remove this line
        if hasattr(post, "published_at"):
            post.published_at = datetime.utcnow()
        db.session.commit()
        return

    # 4. Enqueue one job per platform row
    q = get_queue()
    enqueued_any = False
    for pp in pps:
        if pp.status in ("queued", "publishing", "published", "skipped"):
            current_app.logger.info(f"[tasks.publish_post] skip pp_id={pp.id} status={pp.status}")
            continue

        pp.status = "queued"
        db.session.commit()

        #! Enqueue immediately. If you want scheduled publication, use q.enqueue_at(run_at_utc, publish_post_platform, pp.id)
        q.enqueue(publish_post_platform, pp.id)
        enqueued_any = True
        current_app.logger.info(f"[tasks.publish_post] enqueued pp_id={pp.id}")

    # 5. Update parent post aggregate status
    _recompute_parent_post_status(post.id)

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
        # Some succeeded, some failed/skipped
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
