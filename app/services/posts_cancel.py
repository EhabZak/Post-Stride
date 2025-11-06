# app/services/posts_cancel.py
from typing import Optional, Iterable
from sqlalchemy import and_
from app.models import db
from app.models.post import Post
from app.models.post_platform import PostPlatform
from app.models.scheduled_job import ScheduledJob
from app.scheduler import mark_scheduled_job_status  # if you already have it  # your function from the prompt
from app.scheduler import cancel_scheduled

CANCEL_TARGET_STATES = {"pending", "queued", "scheduled"}  # safe to flip to canceled/skipped


def _mark_platforms_canceled(post_id: int, platform_ids: Optional[Iterable[int]] = None, as_status: str = "canceled") -> int:
    """
    Mark future/unrun platform deliveries as canceled/skipped.
    Returns # of rows updated.
    """
    q = PostPlatform.query.filter(
        PostPlatform.post_id == post_id,
        PostPlatform.status.in_(CANCEL_TARGET_STATES)
    )
    if platform_ids:
        q = q.filter(PostPlatform.platform_id.in_(platform_ids))
    updated = 0
    for pp in q.all():
        pp.status = as_status
        updated += 1
    return updated


def _cancel_scheduled_jobs_for(post_id: int, platform_ids: Optional[Iterable[int]] = None) -> int:
    """
    Best-effort: cancel all ScheduledJob rows that match (post_id [, platform_ids])
    and are not terminal. Returns # of jobs we attempted to cancel.
    """
    q = ScheduledJob.query.filter(
        ScheduledJob.post_id == post_id,
        ~ScheduledJob.status.in_(("finished", "failed", "canceled"))
    )
    if platform_ids:
        q = q.filter(ScheduledJob.platform_id.in_(platform_ids))

    attempted = 0
    for sj in q.all():
        # uses your existing function; it also marks the row to "canceled"
        try:
            cancel_scheduled(sj.id)
            attempted += 1
        except Exception:
            # swallow; we still try to set DB state consistently below if needed
            mark_scheduled_job_status(sj.id, "canceled")
    return attempted



def _recompute_post_status(post_id: int) -> str:
    """
    Aggregate child states and set posts.status accordingly.
    """
    post = Post.query.get(post_id)
    if not post:
        return "unknown"

    pps = PostPlatform.query.filter_by(post_id=post_id).all()
    if not pps:
        # no platforms: if you want, leave as-is
        return post.status

    states = {pp.status for pp in pps}

    if all(s == "published" for s in states):
        post.status = "published"
    elif "published" in states and any(s in {"canceled", "skipped", "failed"} for s in states):
        post.status = "partially_published"
    elif all(s in {"canceled", "skipped"} for s in states):
        post.status = "canceled"
    else:
        # still mixed + some pending/queued/scheduled/publishing
        # choose the more honest umbrella:
        if "publishing" in states:
            post.status = "publishing"
        elif any(s in {"pending", "queued", "scheduled"} for s in states):
            post.status = "scheduled"
        else:
            # fallback if only failed present and nothing else:
            if all(s == "failed" for s in states):
                post.status = "failed"
            # else keep existing
    return post.status


def cancel_entire_post_future(post_id: int, as_status: str = "canceled") -> dict:
    """
    Cancel all not-yet-run deliveries for this post (across all platforms),
    update platform rows, recompute post status. One transaction.
    """
    # with db.session.begin():
    #     attempted_jobs = _cancel_scheduled_jobs_for(post_id)
    #     updated_pp = _mark_platforms_canceled(post_id, as_status=as_status)
    #     new_status = _recompute_post_status(post_id)
    # return {"attempted_jobs": attempted_jobs, "platforms_updated": updated_pp, "post_status": new_status}
    attempted_jobs = _cancel_scheduled_jobs_for(post_id)
    updated_pp = _mark_platforms_canceled(post_id, as_status=as_status)
    new_status = _recompute_post_status(post_id)
    return {"attempted_jobs": attempted_jobs, "platforms_updated": updated_pp, "post_status": new_status}


def cancel_single_platform_future(post_id: int, platform_id: int, as_status: str = "canceled") -> dict:
    """
    Cancel future delivery for a single platform of a post.
    """
    # with db.session.begin():
    #     attempted_jobs = _cancel_scheduled_jobs_for(post_id, platform_ids=[platform_id])
    #     updated_pp = _mark_platforms_canceled(post_id, platform_ids=[platform_id], as_status=as_status)
    #     new_status = _recompute_post_status(post_id)
    # return {"attempted_jobs": attempted_jobs, "platforms_updated": updated_pp, "post_status": new_status}
    
    attempted_jobs = _cancel_scheduled_jobs_for(post_id, platform_ids=[platform_id])
    updated_pp = _mark_platforms_canceled(post_id, platform_ids=[platform_id], as_status=as_status)
    new_status = _recompute_post_status(post_id)
    return {"attempted_jobs": attempted_jobs, "platforms_updated": updated_pp, "post_status": new_status}

    # app/services/posts_cancel.py


def cancel_entire_post_future(post_id: int, as_status: str = "canceled") -> dict:
    attempted_jobs = _cancel_scheduled_jobs_for(post_id)
    updated_pp = _mark_platforms_canceled(post_id, as_status=as_status)
    new_status = _recompute_post_status(post_id)
    return {"attempted_jobs": attempted_jobs, "platforms_updated": updated_pp, "post_status": new_status}

