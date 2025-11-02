"""
Centralized scheduler helpers for one-time + recurring schedules.

TIMEZONE CONVENTION:
- All scheduling operations expect naive UTC datetimes
- _to_utc_naive() normalizes any datetime to naive UTC for consistency
- Database stores naive UTC; API layer handles user timezone conversion
"""
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
# def schedule_post_at(post_id: int, when: datetime, job_id: Optional[str] = None,
#                      meta: Optional[Dict[str, Any]] = None) -> Job:
#     run_at = _to_utc_naive(when)
#     q = get_queue()  # <-- get the live queue
#     return q.enqueue_at(
#         run_at,
#         JOB_FUNC_PATH,
#         post_id,
#         job_id=job_id,
#         retry=_retry_policy(),
#         meta=meta or {"post_id": post_id}
#     )
def schedule_post_at(post_id: int, when: datetime, job_id: Optional[str] = None,
                     meta: Optional[Dict[str, Any]] = None) -> Job:
    # import the callable, not a string path
    from app.tasks import publish_post
    run_at = _to_utc_naive(when)
    scheduler = _get_scheduler()  # Scheduler(queue=get_queue(), connection=redis_conn)
    return scheduler.enqueue_at(
        run_at,
        publish_post,              # <-- callable (not "app.tasks.publish_post")
        post_id,
        job_id=job_id,                 # <-- rq-scheduler uses 'id=' for job_id
        meta=meta or {"post_id": post_id},
        # retry=_retry_policy(),     # (passes through to queue when enqueued)
    )

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
def cancel_scheduled(job_id: str) -> bool:
    job = fetch_job(job_id)
    if not job:
        return False
    try:
        job.cancel()
        return True
    except Exception:
        return False

#! reschedule ///////////////////////////////////////////////////////////////////////////
'''
This function is used to reschedule a job.
'''
def reschedule(job_id: str, new_when: datetime) -> Optional[Job]:
    job = fetch_job(job_id)
    if not job:
        return None
    try:
        job.cancel()
    except Exception:
        pass
    args = job.args or ()
    kwargs = job.kwargs or {}
    func_path = job.func_name or JOB_FUNC_PATH
    run_at = _to_utc_naive(new_when)
    q = get_queue()
    return q.enqueue_at(run_at, func_path, *args, **kwargs)

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