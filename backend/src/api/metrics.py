import shutil

import psutil
from fastapi import APIRouter

metrics_router = APIRouter()


@metrics_router.get("/healthz")
def health_check():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    return {
        "status": "ok",
        "cpu_percent": cpu_percent,
        "memory": {
            "total_mb": round(memory.total / 1024**2, 2),
            "used_mb": round(memory.used / 1024**2, 2),
            "percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 2),
            "used_gb": round(disk.used / 1024**3, 2),
            "percent": round(disk.used / disk.total * 100, 2),
        },
    }


@metrics_router.get("/system")
def system_metrics():
    pass


@metrics_router.get("/logs")
def get_logs():
    pass
