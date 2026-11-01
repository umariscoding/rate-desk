import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.container import build_container, create_cominty_client
from app.interface.api.error_handlers import register_error_handlers
from app.interface.api.router import api_router

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx logs full URLs, including presigned signatures.


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with create_cominty_client(settings) as client:
            app.state.container = build_container(settings, client)
            yield

    app = FastAPI(title="Rate Desk", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.allowed_origins, allow_methods=["*"], allow_headers=["*"]
    )
    register_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
