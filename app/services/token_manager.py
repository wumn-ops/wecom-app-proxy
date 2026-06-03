from __future__ import annotations

import asyncio
import logging
import time

import httpx

from app.core.exceptions import TokenRefreshError

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(
        self,
        corp_id: str,
        corp_secret: str,
        http_client: httpx.AsyncClient,
        base_url: str,
        refresh_buffer: int = 300,
    ):
        self._corp_id = corp_id
        self._corp_secret = corp_secret
        self._http_client = http_client
        self._base_url = base_url
        self._refresh_buffer = refresh_buffer
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        if self._token and time.time() + self._refresh_buffer < self._expires_at:
            return self._token

        async with self._lock:
            if self._token and time.time() + self._refresh_buffer < self._expires_at:
                return self._token

            url = (
                f"{self._base_url}/cgi-bin/gettoken"
                f"?corpid={self._corp_id}&corpsecret={self._corp_secret}"
            )
            try:
                resp = await self._http_client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                raise TokenRefreshError(f"获取 access_token 失败: {e}") from e

            data = resp.json()
            if data.get("errcode", -1) != 0:
                raise TokenRefreshError(
                    f"获取 access_token 失败 [{data.get('errcode')}]: {data.get('errmsg')}"
                )

            self._token = data["access_token"]
            self._expires_at = time.time() + data.get("expires_in", 7200)
            logger.info("access_token 已刷新，过期时间: %s", self._expires_at)
            return self._token  # type: ignore[return-value]
