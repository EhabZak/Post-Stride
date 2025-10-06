# # app/scheduler.py
# """
# Centralized helpers for one-time + recurring schedules.

# - One-time: uses RQ's queue.enqueue_at(...) so it behaves exactly like your route today.
# - Recurring/cron: uses rq-scheduler's Scheduler(...).schedule(...).

# NOTE: To make delayed jobs/recurring jobs actually fire in production, you must run:
#     rqscheduler --queue poststride-tasks --url $REDIS_URL

# Your existing worker keeps `with_scheduler=True`, which is fine; running the external
# rqscheduler makes promotions resilient even if no worker is idle.
# """

# from __future__ import annotations

# from datetime import datetime, timedelta, timezone
# from typing import Optional, List, Dict, Any

# from rq import Retry
# from rq.job import Job
# from rq.registry import ScheduledJobRegistry
# from rq_scheduler import Scheduler

# from app.extensions.queue import redis_conn, task_queue
# # Import the callable path as a string to avoid circular imports at import time
# JOB_FUNC_PATH = "app.tasks.publish_post"


# # =============================================================================
# # Internals / Utilities
# # =============================================================================

# def _to_utc_naive(dt: datetime) -> datetime:
#     """
#     Normalize any datetime to UTC-naive (matching what you already do in routes).
#     - If dt has tzinfo, convert to UTC then drop tzinfo.
#     - If dt is naive, assume it's already UTC.
#     """
#     if dt.tzinfo is not None:
#         return dt.astimezone(timezone.utc).replace(tzinfo=None)
#     return dt


# def _retry_policy() -> Retry:
#     """
#     Standard retry policy (same flavor you used in your route).
#     Adjust as you like.
#     """
#     return Retry(max=3, interval=[60, 300, 900])


# def _scheduled_registry() -> ScheduledJobRegistry:
#     """Convenience accessor for the scheduled jobs registry on your queue."""
#     return ScheduledJobRegistry(queue=task_queue)


# def _get_scheduler() -> Scheduler:
#     """
#     Dedicated rq-scheduler instance tied to your existing queue + connection.
#     Only needed for recurring/cron. Safe to create on-demand.
#     """
#     return Scheduler(queue=task_queue, connection=redis_conn)


# # =============================================================================
# # Public API — One-time scheduling (same behavior as q.enqueue_at in your route)
# # =============================================================================

# def schedule_post_at(post_id: int, when: datetime, job_id: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> Job:
#     """
#     Enqueue a single run of `app.tasks.publish_post` at an exact UTC time.
#     Returns the RQ Job object.

#     This mirrors your route's q.enqueue_at(...) so you can use it interchangeably.
#     """
#     run_at = _to_utc_naive(when)
#     return task_queue.enqueue_at(
#         run_at,
#         JOB_FUNC_PATH,
#         post_id,
#         job_id=job_id,
#         retry=_retry_policy(),
#         meta=meta or {"post_id": post_id}
#     )


# def list_scheduled_job_ids() -> List[str]:
#     """
#     Return job IDs currently in the Scheduled registry for your queue.
#     Useful for admin/status endpoints.
#     """
#     return _scheduled_registry().get_job_ids()


# def fetch_job(job_id: str) -> Optional[Job]:
#     """Fetch a Job by id (or None if missing)."""
#     try:
#         return Job.fetch(job_id, connection=redis_conn)
#     except Exception:
#         return None


# def cancel_scheduled(job_id: str) -> bool:
#     """
#     Cancel a scheduled job (moves it to the Canceled registry).
#     Returns True if we found & canceled it, False otherwise.
#     """
#     job = fetch_job(job_id)
#     if not job:
#         return False
#     try:
#         job.cancel()
#         return True
#     except Exception:
#         return False


# def reschedule(job_id: str, new_when: datetime) -> Optional[Job]:
#     """
#     Reschedule by: cancel -> enqueue_at(new_time).
#     Returns the new Job (with a NEW id) or None if original not found.
#     """
#     job = fetch_job(job_id)
#     if not job:
#         return None
#     # Try to cancel the old one; ignore failures and proceed.
#     try:
#         job.cancel()
#     except Exception:
#         pass

#     # Re-enqueue with a fresh id; you can generate your own stable ID if needed.
#     args = job.args or ()
#     kwargs = job.kwargs or {}

#     # If the original job wasn't our publish, we still try to keep parity
#     func_path = job.func_name or JOB_FUNC_PATH
#     run_at = _to_utc_naive(new_when)

#     return task_queue.enqueue_at(
#         run_at,
#         func_path,
#         *args,
#         **kwargs
#     )


# # =============================================================================
# # Public API — Recurring / cron-like (requires the external `rqscheduler` process)
# # =============================================================================

# def ensure_recurring_publish_demo(interval_minutes: int = 15) -> str:
#     """
#     Example: register a recurring job that calls publish_post with a dummy post_id=-1
#     every `interval_minutes`. Uses a fixed job id to stay idempotent across restarts.

#     Call this ONCE at startup (e.g., from create_app) or from an admin task.
#     """
#     scheduler = _get_scheduler()
#     job_id = "recurring:publish_post:demo"

#     # If a job with the same id already exists, rq-scheduler replaces or reuses it.
#     scheduler.schedule(
#         scheduled_time=datetime.utcnow() + timedelta(minutes=1),
#         func=JOB_FUNC_PATH,
#         args=[-1],
#         interval=interval_minutes * 60,  # seconds
#         repeat=None,                     # forever
#         id=job_id,
#         meta={"purpose": "demo recurring publish"}
#     )
#     return job_id


# def ensure_recurring(func: str,
#                      args: Optional[List[Any]] = None,
#                      kwargs: Optional[Dict[str, Any]] = None,
#                      *,
#                      job_id: str,
#                      start_in: timedelta = timedelta(minutes=1),
#                      every: timedelta = timedelta(minutes=10),
#                      meta: Optional[Dict[str, Any]] = None) -> str:
#     """
#     Generic recurring registrar. Idempotent if you reuse the same `job_id`.

#     Example:
#         ensure_recurring(
#             func="app.tasks.refresh_tokens",
#             args=[],
#             kwargs={},
#             job_id="recurring:refresh_tokens:6h",
#             every=timedelta(hours=6),
#         )
#     """
#     scheduler = _get_scheduler()
#     scheduler.schedule(
#         scheduled_time=datetime.utcnow() + start_in,
#         func=func,
#         args=args or [],
#         kwargs=kwargs or {},
#         interval=int(every.total_seconds()),
#         repeat=None,
#         id=job_id,
#         meta=meta or {}
#     )
#     return job_id


# def cancel_recurring(job_id: str) -> bool:
#     """
#     Cancel a recurring job previously registered with `ensure_recurring*`.
#     Returns True if deletion succeeded, False otherwise.
#     """
#     scheduler = _get_scheduler()
#     try:
#         # rq-scheduler keeps its own job store; use cancel/delete there
#         job = scheduler.job_class.fetch(job_id, connection=redis_conn)
#         scheduler.cancel(job)
#         return True
#     except Exception:
#         return False


# # =============================================================================
# # Optional: seed recurring tasks when run directly
# # =============================================================================

# # if __name__ == "__main__":
# #     # Example: register the demo recurring task.
# #     # You can comment this out; it’s here for quick/manual seeding.
# #     jid = ensure_recurring_publish_demo(interval_minutes=15)
# #     print(f"Recurring job ensured: {jid}")
# #     print("Tip: remember to run `rqscheduler --queue poststride-tasks --url $REDIS_URL`.")
# app/scheduler.py
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

JOB_FUNC_PATH = "app.tasks.publish_post"

def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

def _retry_policy() -> Retry:
    return Retry(max=3, interval=[60, 300, 900])

def _scheduled_registry() -> ScheduledJobRegistry:
    # bind to the currently initialized queue
    return ScheduledJobRegistry(queue=get_queue())

def _get_scheduler() -> Scheduler:
    # tie scheduler to the same queue/connection
    return Scheduler(queue=get_queue(), connection=redis_conn)

def schedule_post_at(post_id: int, when: datetime, job_id: Optional[str] = None,
                     meta: Optional[Dict[str, Any]] = None) -> Job:
    run_at = _to_utc_naive(when)
    q = get_queue()  # <-- get the live queue
    return q.enqueue_at(
        run_at,
        JOB_FUNC_PATH,
        post_id,
        job_id=job_id,
        retry=_retry_policy(),
        meta=meta or {"post_id": post_id}
    )

def list_scheduled_job_ids() -> List[str]:
    return _scheduled_registry().get_job_ids()

def fetch_job(job_id: str) -> Optional[Job]:
    try:
        return Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return None

def cancel_scheduled(job_id: str) -> bool:
    job = fetch_job(job_id)
    if not job:
        return False
    try:
        job.cancel()
        return True
    except Exception:
        return False

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

