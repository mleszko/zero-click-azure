from __future__ import annotations

from fastapi import FastAPI

from api.routes import router as api_router
from core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title='Self-Correcting AI Agent API',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)
app.include_router(api_router)
