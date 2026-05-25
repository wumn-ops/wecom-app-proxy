import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.v1.callback import router as callback_router
from app.api.v1.router import router as v1_router
from app.core.exceptions import TokenRefreshError, WeComApiError, WeComHttpError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="WeCom Message Center", version="0.1.0")

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
