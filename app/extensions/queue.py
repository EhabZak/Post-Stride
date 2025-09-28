#! hold redis_conn & task_queue
from typing import Optional
from redis import Redis
from rq import Queue


#! redis_conn & task_queue ///////////////////////////////////////////////////////////////////////////
redis_conn: Optional[Redis] = None
task_queue: Optional[Queue] = None

#! init_redis ///////////////////////////////////////////////////////////////////////////
def init_redis(redis_url: str) -> None:
    global redis_conn, task_queue
    redis_conn = Redis.from_url(redis_url) # Create a Redis client connection (used by RQ Queue to store and fetch jobs)
    task_queue = Queue("poststride-tasks", connection=redis_conn) # this is the RQ queue//////////////////////

#! get_queue ///////////////////////////////////////////////////////////////////////////
def get_queue() -> Queue:
    if task_queue is None:
        raise RuntimeError("RQ queue not initialized. Call init_redis() in app factory.")
    return task_queue