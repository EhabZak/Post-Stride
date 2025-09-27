#! hold redis_conn & task_queue
from redis import Redis
from rq import Queue

redis_conn = None
task_queue = None

def init_redis(redis_url):
    global redis_conn, task_queue
    redis_conn = Redis.from_url(redis_url)
    task_queue = Queue("poststride-tasks", connection=redis_conn)