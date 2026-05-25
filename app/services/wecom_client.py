import httpx

from app.core.exceptions import WeComApiError, WeComHttpError
from app.models.common import WeComApiResponse
from app.models.template_card import SendTemplateCardRequest
from app.services.token_manager import TokenManager


class WeComClient:
    def __init__(self, token_manager: TokenManager, base_url: str):
        self._token_manager = token_manager
        self._base_url = base_url
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))

    async def send_template_card(self, req: SendTemplateCardRequest, agentid: int) -> WeComApiResponse:
        token = await self._token_manager.get_token()
        payload = req.model_dump(exclude_none=True)
        payload["msgtype"] = "template_card"
        payload["agentid"] = agentid

        try:
            resp = await self._http_client.post(
                f"{self._base_url}/cgi-bin/message/send?access_token={token}",
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise WeComHttpError(f"发送模板卡片失败: {e}") from e

        data = resp.json()
        errcode = data.get("errcode", -1)
        if errcode != 0:
            raise WeComApiError(errcode, data.get("errmsg", "unknown error"))

        return WeComApiResponse(**data)
