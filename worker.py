# worker.py (at repo root or app/worker.py — pick one and adjust paths)
import os, sys
sys.path.append(os.path.dirname(__file__))

# from rq import Worker, Connection
from rq import Worker 
from app import app as flask_app                
from app.extensions.queue import redis_conn, task_queue



# Push app context BEFORE importing tasks to avoid circular imports
flask_app.app_context().push()

# Importing app.tasks will also import app/__init__.py and build the global app
import app.tasks  # noqa: F401 - needed to register tasks with RQ



if __name__ == "__main__":
    # with Connection(redis_conn):
        # this is the alternative to using rqscheduler.Scheduler() but it is a small set up for a single worker
        #  if you want to scale up you need use the rqscheduler.Scheduler()
        # Worker([task_queue]).work(with_scheduler=False) 
        worker = Worker([task_queue], connection=redis_conn)  # pass connection=
        worker.work(with_scheduler=False)
