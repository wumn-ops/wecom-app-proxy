from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.dependencies import get_settings, get_wecom_client
from app.models.common import WeComApiResponse
from app.models.template_card import SendTemplateCardRequest
from app.services.wecom_client import WeComClient

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/template-card", response_model=WeComApiResponse)
async def send_template_card(
    req: SendTemplateCardRequest,
    settings: Settings = Depends(get_settings),
    client: WeComClient = Depends(get_wecom_client),
) -> WeComApiResponse:
    if not req.touser and not req.toparty and not req.totag:
        if settings.wecom_default_touser:
            req.touser = settings.wecom_default_touser
        else:
            raise HTTPException(
                status_code=422,
                detail="至少需要指定 touser、toparty 或 totag 中的一个，或在 .env 中配置 WECOM_DEFAULT_TOUSER",
            )

    return await client.send_template_card(req, agentid=settings.wecom_agent_id)
