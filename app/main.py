from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal, engine
from app.services.seeds import seed_sources
from app.web.routes import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        if inspect(engine).has_table("scrape_sources"):
            seed_sources(db)
    finally:
        db.close()
    yield


configure_logging()

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_router)
app.include_router(web_router)


@app.get("/health")
def health():
    return {"status": "ok"}
