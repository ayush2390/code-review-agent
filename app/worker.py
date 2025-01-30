from celery import Celery
from .agent import CodeReviewAgent
from .config import Settings
import logging

settings = Settings()
celery_app = Celery('code_review',
                    broker=settings.CELERY_BROKER_URL,
                    backend=settings.CELERY_RESULT_BACKEND)

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url: str, pr_number: int, github_token: str | None = None):
    try:
        agent = CodeReviewAgent(settings.LLM_API_KEY)
        return agent.analyze_pr(repo_url, pr_number, github_token)
    except Exception as e:
        logger.error(f"Error analyzing PR: {str(e)}")
        raise
