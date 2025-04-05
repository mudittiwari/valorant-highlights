from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import time
import subprocess
import torch
import multiprocessing as mp
from redis import Redis
from rq import Queue
from worker import process_video_task

redis_conn = Redis()
task_queue = Queue("video_tasks", connection=redis_conn)
app = FastAPI()
QUEUE_THRESHOLD = 30
RATE_LIMIT_SECONDS = 1
# mp.set_start_method("spawn", force=True)

class ProcessRequest(BaseModel):
    youtube_url: str
    start_time: str
    end_time: str
    player_names: list[str]
    email: str

@app.post("/process")
def enqueue_job(req: ProcessRequest):
    ip = "user"
    rate_key = f"ratelimit:{ip}"
    if redis_conn.exists(rate_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded, try again later.")
    redis_conn.set(rate_key, 1, ex=RATE_LIMIT_SECONDS)
    if len(task_queue.jobs) >= QUEUE_THRESHOLD:
        raise HTTPException(status_code=503, detail="Too many requests in queue. Try again later.")
    
    job = task_queue.enqueue_call(
        func=process_video_task,
        args=(req.youtube_url, req.start_time, req.end_time, req.player_names, req.email)
    )
    # print(job)
    return {"job_id": job.get_id(), "status": "queued"}
