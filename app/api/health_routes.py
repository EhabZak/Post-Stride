"""
GET /api/health – liveness/readiness probe.

"""

from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from app.models import db
import os, shutil, time
import redis
from rq import Queue

health_bp = Blueprint("health", __name__, url_prefix="/api/health")

#//redis ///////////////////////////////////////////////////////////////////////////
# init redis client once (or inject)
def get_redis():
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, socket_connect_timeout=0.2, socket_timeout=0.2)

REDIS = get_redis()
RQ_QUEUE = Queue("default", connection=REDIS)

START_TIME = time.time()

@health_bp.route("/live", methods=["GET"])
def live():
    return jsonify({
        "status": "ok",
        "uptime_sec": int(time.time() - START_TIME)
    }), 200

@health_bp.route("/ready", methods=["GET"])
def ready():
    checks = {}
    overall = "healthy"
#! Ready ///////////////////////////////////////////////////////////////////////////
    # DB
    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception:
        checks["database"] = {"status": "unhealthy"}
        overall = "unhealthy"
#! Redis ///////////////////////////////////////////////////////////////////////////
    # Redis (optional for now)
    try:
        REDIS.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception:
        checks["redis"] = {"status": "unhealthy"}
        # Don't make overall unhealthy if Redis fails (optional service)
#! Queue ///////////////////////////////////////////////////////////////////////////
    # Queue depth (quick stat, not a gate)
    try:
        checks["queue"] = {"status": "healthy", "backlog": RQ_QUEUE.count}
    except Exception:
        checks["queue"] = {"status": "unknown"}
#! Environment ///////////////////////////////////////////////////////////////////////////
    # Env presence (don’t list secrets)
    required = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        checks["environment"] = {"status": "unhealthy", "missing": len(missing)}
        overall = "unhealthy"
    else:
        checks["environment"] = {"status": "healthy"}
#! Disk ///////////////////////////////////////////////////////////////////////////
    # Disk space (optional threshold: 500MB)
    total, used, free = shutil.disk_usage("/")
    if free < 500 * 1024 * 1024:
        checks["disk"] = {"status": "unhealthy", "free_bytes": free}
        overall = "unhealthy"
    else:
        checks["disk"] = {"status": "healthy"}
#! Code ///////////////////////////////////////////////////////////////////////////
    code = 200 if overall == "healthy" else 503
    return jsonify({"status": overall, "checks": checks}), code
