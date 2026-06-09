from fastapi import APIRouter

from app.api.routes import jobs, scrape_jobs, sources


api_router = APIRouter()
api_router.include_router(jobs.router)
api_router.include_router(scrape_jobs.router)
api_router.include_router(sources.router)