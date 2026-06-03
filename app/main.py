import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.v1.callback import router as callback_router
from app.api.v1.router import router as v1_router
from app.config import Settings
from app.core.exceptions import TokenRefreshError, WeComApiError, WeComHttpError
from app.services.scheduler import CronScheduler
from app.services.token_manager import TokenManager
from app.services.wecom_client import WeComClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler = None
        http_client = None
        if settings.cron_schedule and settings.wecom_default_touser and settings.smartsheet_page_url:
            http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
            token_mgr = TokenManager(
                corp_id=settings.wecom_corp_id,
                corp_secret=settings.wecom_corp_secret,
                http_client=http_client,
                base_url=settings.wecom_api_base_url,
                refresh_buffer=settings.wecom_token_refresh_buffer,
            )
            client = WeComClient(token_mgr, settings.wecom_api_base_url)
            scheduler = CronScheduler(
                cron_expr=settings.cron_schedule,
                client=client,
                touser=settings.wecom_default_touser,
                agent_id=settings.wecom_agent_id,
                page_url=settings.smartsheet_page_url,
            )
            scheduler.start()
            logger.info("定时任务已启动: %s", settings.cron_schedule)
        else:
            logger.info("定时任务未配置（缺少 cron_schedule / touser / page_url）")

        yield

        if scheduler:
            scheduler.stop()
        if http_client:
            await http_client.aclose()

    app = FastAPI(title="WeCom Message Center", version="0.1.0", lifespan=lifespan, redirect_slashes=False)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)
    app.include_router(callback_router)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
        return html_path.read_text(encoding="utf-8")

    @app.get("/smartsheet", response_class=HTMLResponse)
    async def smartsheet_page():
        html_path = Path(__file__).resolve().parent.parent / "static" / "smartsheet.html"
        return html_path.read_text(encoding="utf-8")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.exception_handler(WeComApiError)
    async def wecom_error_handler(request: Request, exc: WeComApiError):
        status = 401 if 40001 <= exc.errcode <= 40014 else 502
        return JSONResponse(
            status_code=status,
            content={"errcode": exc.errcode, "errmsg": exc.errmsg},
        )

    @app.exception_handler(TokenRefreshError)
    async def token_error_handler(request: Request, exc: TokenRefreshError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(WeComHttpError)
    async def http_error_handler(request: Request, exc: WeComHttpError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    return app


app = create_app()
