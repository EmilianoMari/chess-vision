"""Gunicorn configuration for Chess Vision API."""

import multiprocessing
import os

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8002')}"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
keepalive = 5

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Process naming
proc_name = "chess-vision"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"Starting Chess Vision API on {bind}")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Chess Vision API ready - {workers} workers")

def on_exit(server):
    """Called just before the master process exits."""
    print("Chess Vision API shutting down")
