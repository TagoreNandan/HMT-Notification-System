import logging
from api.watchlist import router as watchlist_router
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.account import router as account_router
from api.auth import router as auth_router
from api.notifications import router as notifications_router
from api.rate_limit import limiter
from api.routes import router
from config import get_settings
from db.session import init_db
from scheduler import start_scheduler, stop_scheduler
from typing import cast
from starlette.types import ExceptionHandler
from api.catalog import router as catalog_router
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s", settings.app_name)
    logger.info(
        "Database URL scheme: %s", settings.sqlalchemy_database_url.split(":", 1)[0]
    )
    init_db()
    if settings.enable_scheduler:
        start_scheduler()
    else:
        logger.info("Scheduler disabled via ENABLE_SCHEDULER=False setting")
    yield
    if settings.enable_scheduler:
        stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    cast(ExceptionHandler, _rate_limit_exceeded_handler),
)
app.add_middleware(SlowAPIMiddleware)

app.include_router(auth_router)
app.include_router(account_router)
app.include_router(router)
app.include_router(notifications_router)
app.include_router(catalog_router)
app.include_router(watchlist_router)
