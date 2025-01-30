from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from .worker import analyze_pr_task
from .config import Settings

app = FastAPI(title="Code Review Agent")
settings = Settings()

class PRAnalysisRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: str | None = None


@app.get("/")
async def get_root():
    return {"messg": "hello There"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    result = AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status}

@app.get("/results/{task_id}")
async def get_results(task_id: str):
    result = AsyncResult(task_id)
    if not result.ready():
        raise HTTPException(status_code=404, message="Task not completed")
    return result.get()
