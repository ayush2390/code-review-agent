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

