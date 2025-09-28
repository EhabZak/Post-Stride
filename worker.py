# worker.py (at repo root or app/worker.py — pick one and adjust paths)
import os, sys
sys.path.append(os.path.dirname(__file__))

from rq import Worker, Connection

# Importing app.tasks will also import app/__init__.py and build the global app
import app.tasks  # noqa: F401 - needed to register tasks with RQ

from app.extensions.queue import redis_conn, task_queue

if __name__ == "__main__":
    with Connection(redis_conn):
        Worker([task_queue]).work(with_scheduler=True)