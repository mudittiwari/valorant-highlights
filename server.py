from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
import time
import subprocess
import torch
import multiprocessing as mp
from redis import Redis
from rq import Queue
from worker import process_video_task
from fastapi.middleware.cors import CORSMiddleware
import logging
from routes.user_routes import router as user_router
from routes.match_routes import router as match_router
from crud import create_match, get_user_matches, get_user_by_email, update_match_status
from models import ProcessRequest
from dependencies import create_match_from_request, get_current_user
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logging.getLogger("pymongo").setLevel(logging.ERROR)



redis_conn = Redis(host="redis", port=6379)
task_queue = Queue("video_tasks", connection=redis_conn)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QUEUE_THRESHOLD = 30
RATE_LIMIT_SECONDS = 1
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(match_router, prefix="/matches", tags=["matches"])
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server (if applicable)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        
    allow_credentials=True,
    allow_methods=["*"],             
    allow_headers=["*"],           
)


@app.on_event("startup")
async def startup_event():
    logger.info("✅ FastAPI server is starting...")


@app.post("/process")
async def enqueue_job(req: ProcessRequest, current_user: dict = Depends(get_current_user)):
    # logger.info("hello how are you")
    user = await get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist")
    created_match = await create_match(create_match_from_request(req, req.email))
    ip = "user"
    rate_key = f"ratelimit:{ip}"
    if redis_conn.exists(rate_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded, try again later.")
    redis_conn.set(rate_key, 1, ex=RATE_LIMIT_SECONDS)
    if len(task_queue.jobs) >= QUEUE_THRESHOLD:
        raise HTTPException(status_code=503, detail="Too many requests in queue. Try again later.")
    job = task_queue.enqueue_call(
        func=process_video_task,
        args=(req.youtube_url, req.start_time, req.end_time, req.player_names, req.email, created_match.id),
        timeout=3600
    )
    # print(created_match.id)
    return {"job_id": job.get_id(), "status": "in_queue"}
