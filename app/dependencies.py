from __future__ import annotations

import asyncio
from functools import lru_cache

import httpx
from fastapi import Depends

from app.config import Settings
from app.services.token_manager import TokenManager
from app.services.wecom_client import WeComClient

_token_manager: TokenManager | None = None
_wecom_client: WeComClient | None = None
_tm_lock = asyncio.Lock()
_client_lock = asyncio.Lock()


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_token_manager(
    settings: Settings = Depends(get_settings),
) -> TokenManager:
    global _token_manager
    if _token_manager is None:
        async with _tm_lock:
            if _token_manager is None:
                client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
                _token_manager = TokenManager(
                    corp_id=settings.wecom_corp_id,
                    corp_secret=settings.wecom_corp_secret,
                    http_client=client,
                    base_url=settings.wecom_api_base_url,
                    refresh_buffer=settings.wecom_token_refresh_buffer,
                )
    return _token_manager


async def get_wecom_client(
    settings: Settings = Depends(get_settings),
) -> WeComClient:
    global _wecom_client
    if _wecom_client is None:
        async with _client_lock:
            if _wecom_client is None:
                tm = await get_token_manager(settings)
                _wecom_client = WeComClient(tm, settings.wecom_api_base_url)
    return _wecom_client
