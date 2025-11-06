"""
Centralized scheduler helpers for one-time + recurring schedules.

TIMEZONE CONVENTION:
- All scheduling operations expect naive UTC datetimes
- _to_utc_naive() normalizes any datetime to naive UTC for consistency
- Database stores naive UTC; API layer handles user timezone conversion
"""
import importlib
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from rq import Retry
from rq.job import Job
from rq.registry import ScheduledJobRegistry
from rq_scheduler import Scheduler



from app.extensions.queue import get_queue, redis_conn

# JOB_FUNC_PATH = "app.tasks.publish_post"
#! _to_utc_naive ///////////////////////////////////////////////////////////////////////////
'''
This function is used to convert a datetime to naive UTC.
'''
def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

#! _retry_policy ///////////////////////////////////////////////////////////////////////////
'''
This function is used to return a retry policy.
'''
def _retry_policy() -> Retry:
    return Retry(max=3, interval=[60, 300, 900])

#! _scheduled_registry ///////////////////////////////////////////////////////////////////////////
'''
This function is used to return a scheduled job registry.
'''
def _scheduled_registry() -> ScheduledJobRegistry:
    # bind to the currently initialized queue
    return ScheduledJobRegistry(queue=get_queue())

#! _get_scheduler ///////////////////////////////////////////////////////////////////////////
'''
This function is used to return a scheduler.
'''
def _get_scheduler() -> Scheduler:
    # tie scheduler to the same queue/connection
    return Scheduler(queue=get_queue(), connection=redis_conn)

#! schedule_post_at ///////////////////////////////////////////////////////////////////////////
'''
This function is used to schedule a post at a specific time. this is the most important function here.

'''

def schedule_post_at(
    post_id: int,
    when: datetime,
    *,
    created_by_user_id: Optional[int] = None,
    platform_id: Optional[int] = None,
    job_type: str = "publish",
    max_retries: int = 0,
    job_id: Optional[str] = None,           # you can pass a custom id
    meta: Optional[Dict[str, Any]] = None,  # extra metadata from caller
):
    """
    DB-aware scheduler that RETURNS the RQ Job object (so caller can use job.id).
    Steps:
      1) Create a scheduled_jobs row
      2) Enqueue via rq-scheduler at the exact time
      3) Persist rq_job_id + enqueued_at to DB
      4) Return the Job object

    NOTE: We also attach 'scheduled_job_id' into job.meta so the worker can
          mark started/finished/failed against the right DB row.
    """
    # Local imports avoid circular import issues
    from app.models import db
    from app.models.scheduled_job import ScheduledJob
    from app.tasks import publish_post

    when_utc = _to_utc_naive(when)
    scheduler = _get_scheduler()
    queue_name = get_queue().name

    # 1) DB row
    sj = ScheduledJob(
        post_id=post_id,
        platform_id=platform_id,
        job_type=job_type,
        queue_name=queue_name,
        status="scheduled",
        scheduled_for=when_utc,
        max_retries=max_retries,
        created_by_user_id=created_by_user_id,
    )
    db.session.add(sj)
    db.session.commit()  # ensure sj.id is available

    # 2) Compute stable job_id if not provided
    if not job_id:
        job_id = f"{job_type}-{post_id}-{sj.id}-{int(when_utc.timestamp())}"

    # Merge meta and inject identifiers for the worker
    meta_payload = {
        **(meta or {}),
        "post_id": post_id,
        "scheduled_job_id": sj.id,
    }

    # 3) Enqueue via rq-scheduler (returns an RQ Job)
    job = scheduler.enqueue_at(
        when_utc,
        publish_post,   # callable
        post_id,
        job_id=job_id,  # rq-scheduler's id
        meta=meta_payload,
        # retry=_retry_policy() if max_retries else None,  # enable when ready
    )

    # 4) Persist rq_job_id to DB
    sj.rq_job_id = job.id
    sj.enqueued_at = datetime.utcnow()
    db.session.commit()

    return job


#! list_scheduled_job_ids ///////////////////////////////////////////////////////////////////////////
'''
This function is used to list scheduled job ids.
'''
def list_scheduled_job_ids() -> List[str]:
    # return _scheduled_registry().get_job_ids()
    s = _get_scheduler()
    return list(s.get_jobs())  # rq-scheduler’s view of future jobs
    

#! fetch_job ///////////////////////////////////////////////////////////////////////////
'''
This function is used to fetch a job by id.
'''
def fetch_job(job_id: str) -> Optional[Job]:
    try:
        return Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return None

#! cancel_scheduled ///////////////////////////////////////////////////////////////////////////
'''
This function is used to cancel a scheduled job.
'''
# def cancel_scheduled(job_id: str) -> bool:
#     try:
#         scheduler = _get_scheduler()
#         job = fetch_job(job_id)
#         if job:
#             scheduler.cancel(job)
#             try:
#                 job.cancel()
#             except Exception:
#                 pass
#             return True

#         # If the job object isn't resolvable, fall back to removing by id.
#         scheduler.remove(job_id)
#         return True
#     except Exception:
#         return False
def cancel_scheduled(scheduled_job_id: int) -> bool:
    """
    Cancel a scheduled job by its DB id.
    - Best-effort cancel in rq-scheduler/RQ
    - Mark scheduled_jobs.status='canceled'
    - Does NOT delete the Post
    """
    # local imports to avoid circulars
    from app.models import db
    from app.models.scheduled_job import ScheduledJob

    sj = ScheduledJob.query.get(scheduled_job_id)
    if not sj:
        return False

    # already terminal? treat as success/no-op
    if sj.status in ("finished", "failed", "canceled"):
        return True

    ok = True
    # try cancel in RQ
    try:
        scheduler = _get_scheduler()
        job = fetch_job(sj.rq_job_id) if sj.rq_job_id else None
        if job:
            try:
                scheduler.cancel(job)
            except Exception:
                pass
            try:
                job.cancel()
            except Exception:
                pass
        try:
            if sj.rq_job_id:
                scheduler.remove(sj.rq_job_id)
        except Exception:
            pass
    except Exception:
        ok = False

    # update DB status only (don’t touch sj.post_id)
    from app.scheduler import mark_scheduled_job_status  # if helper is in same file you can call directly
    mark_scheduled_job_status(scheduled_job_id, "canceled")
    # db.session.commit()
    return ok

#! reschedule ///////////////////////////////////////////////////////////////////////////
'''
This function is used to reschedule a job.
'''
# def reschedule(job_id: str, new_when: datetime) -> Optional[Job]:
#     scheduler = _get_scheduler()
#     job = fetch_job(job_id)
#     if not job:
#         try:
#             scheduler.remove(job_id)
#         except Exception:
#             pass
#         return None
#     try:
#         scheduler.cancel(job)
#     except Exception:
#         try:
#             job.cancel()
#         except Exception:
#             pass
#         try:
#             scheduler.remove(job_id)
#         except Exception:
#             pass
#     args = job.args or ()
#     kwargs = job.kwargs or {}
#     meta = getattr(job, "meta", None) or {}
#     func = getattr(job, "func", None)
#     if not func:
#         func_name = job.func_name
#         if func_name:
#             module_name, _, attr = func_name.rpartition(".")
#             if module_name and attr:
#                 try:
#                     module = importlib.import_module(module_name)
#                     func = getattr(module, attr, None)
#                 except Exception:
#                     func = None
#         if not func:
#             func = func_name
#     run_at = _to_utc_naive(new_when)
#     return scheduler.enqueue_at(
#         run_at,
#         func,
#         *args,
#         job_id=job_id,
#         meta=meta,
#         **kwargs
#     )
def reschedule(
    scheduled_job_id: int,
    new_when: datetime,
    *,
    created_by_user_id: Optional[int] = None,
):
    """
    Reschedule by DB id:
    - Cancel old job (best-effort) and mark old row 'canceled'
    - Create a NEW scheduled_jobs row with the new time
    - Enqueue new RQ job and persist rq_job_id/enqueued_at
    - RETURN the new RQ Job object
    """
    from app.models import db
    from app.models.scheduled_job import ScheduledJob
    from app.tasks import publish_post

    old = ScheduledJob.query.get(scheduled_job_id)
    if not old:
        return None

    # cancel old if not terminal
    if old.status in ("scheduled", "queued", "started"):
        try:
            scheduler = _get_scheduler()
            job = fetch_job(old.rq_job_id) if old.rq_job_id else None
            if job:
                try:
                    scheduler.cancel(job)
                except Exception:
                    pass
                try:
                    job.cancel()
                except Exception:
                    pass
            try:
                if old.rq_job_id:
                    scheduler.remove(old.rq_job_id)
            except Exception:
                pass
        except Exception:
            pass
        mark_scheduled_job_status(old.id, "canceled")
        db.session.commit()

    when_utc = _to_utc_naive(new_when)
    queue_name = get_queue().name

    # create new row
    new_sj = ScheduledJob(
        post_id=old.post_id,
        platform_id=old.platform_id,
        job_type=old.job_type,
        queue_name=queue_name,
        status="scheduled",
        scheduled_for=when_utc,
        max_retries=old.max_retries,
        created_by_user_id=created_by_user_id,
    )
    db.session.add(new_sj)
    db.session.commit()

    # enqueue new job
    scheduler = _get_scheduler()
    job_id = f"{new_sj.job_type}:{new_sj.post_id}:{new_sj.id}:{int(when_utc.timestamp())}"
    job = scheduler.enqueue_at(
        when_utc,
        publish_post,
        new_sj.post_id,
        job_id=job_id,
        meta={"post_id": new_sj.post_id, "scheduled_job_id": new_sj.id},
    )

    # persist RQ metadata
    new_sj.rq_job_id = job.id
    new_sj.enqueued_at = datetime.utcnow()
    db.session.commit()

    return job

#! ensure_recurring_publish_demo ///////////////////////////////////////////////////////////////////////////
'''
This function is used to ensure a recurring publish demo.
'''
def ensure_recurring_publish_demo(interval_minutes: int = 15) -> str:
    scheduler = _get_scheduler()
    job_id = "recurring:publish_post:demo"
    scheduler.schedule(
        scheduled_time=datetime.utcnow() + timedelta(minutes=1),
        func=JOB_FUNC_PATH,
        args=[-1],
        interval=interval_minutes * 60,
        repeat=None,
        id=job_id,
        meta={"purpose": "demo recurring publish"}
    )
    return job_id

#! ensure_recurring ///////////////////////////////////////////////////////////////////////////
'''
This function is used to ensure a recurring job.
'''
def ensure_recurring(func: str,
                     args: Optional[List[Any]] = None,
                     kwargs: Optional[Dict[str, Any]] = None,
                     *,
                     job_id: str,
                     start_in: timedelta = timedelta(minutes=1),
                     every: timedelta = timedelta(minutes=10),
                     meta: Optional[Dict[str, Any]] = None) -> str:
    scheduler = _get_scheduler()
    scheduler.schedule(
        scheduled_time=datetime.utcnow() + start_in,
        func=func,
        args=args or [],
        kwargs=kwargs or {},
        interval=int(every.total_seconds()),
        repeat=None,
        id=job_id,
        meta=meta or {}
    )
    return job_id

#! cancel_recurring ///////////////////////////////////////////////////////////////////////////
'''
This function is used to cancel a recurring job.
I DO NOT USE THIS FUNCTION. I WILL DELETE THIS FUNCTION IF I DO NOT USE IT.
'''
def cancel_recurring(job_id: str) -> bool:
    scheduler = _get_scheduler()
    try:
        job = scheduler.job_class.fetch(job_id, connection=redis_conn)
        scheduler.cancel(job)
        return True
    except Exception:
        return False

# ---- low-level helper (kept separate) ----
def cancel_rq_only(rq_job_id: str) -> bool:
    """
    Cancel in rq-scheduler / RQ by rq_job_id only. No DB updates.
    """
    scheduler = _get_scheduler()
    ok = False
    job = fetch_job(rq_job_id)

    # remove from scheduler
    if job is not None:
        try:
            scheduler.cancel(job); ok = True
        except Exception:
            pass
    try:
        scheduler.remove(rq_job_id); ok = True
    except Exception:
        pass

    # cancel underlying RQ job
    if job is not None:
        try:
            job.cancel(); ok = True
        except Exception:
            pass

    return ok
'''
This function is used to mark a scheduled job status.
'''


def mark_scheduled_job_status(
    scheduled_job_id: int,
    status: str,
    *,
    error_message: Optional[str] = None,
    traceback: Optional[str] = None,
    attempts: Optional[int] = None,
) -> None:
    """
    Update scheduled_jobs.status and standard timestamps.
    Allowed statuses: 'scheduled','queued','started','finished','failed','canceled'
    Safe to call multiple times.
    """
    # Local imports avoid circulars
    from app.models import db
    from app.models.scheduled_job import ScheduledJob

    sj = ScheduledJob.query.get(scheduled_job_id)
    if not sj:
        return

    now = datetime.utcnow()
    sj.status = status

    if status == "started":
        sj.started_at = now
    elif status in ("finished", "failed"):
        sj.finished_at = now
    elif status == "canceled":
        sj.canceled_at = now
    # 'scheduled' / 'queued' don’t change timestamps here

    if attempts is not None:
        sj.attempts = attempts
    if error_message:
        sj.error_message = error_message
    if traceback:
        sj.traceback = traceback

    db.session.commit()