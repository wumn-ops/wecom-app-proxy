import logging
import re
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse, Response

from app.config import Settings
from app.dependencies import get_settings, get_wecom_client
from app.services.crypto import WXBizMsgCrypt, parse_callback_xml
from app.services.message_handler import handle_text_event
from app.services.wecom_client import WeComClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wecom/aibot", tags=["WeCom Callback"])

_crypto: WXBizMsgCrypt | None = None


def get_crypto(settings: Settings = Depends(get_settings)) -> WXBizMsgCrypt:
    global _crypto
    if _crypto is None:
        if not settings.wecom_token or not settings.wecom_encoding_aes_key:
            raise ValueError("回调配置不完整，请在 .env 中设置 WECOM_TOKEN 和 WECOM_ENCODING_AES_KEY")
        _crypto = WXBizMsgCrypt(
            token=settings.wecom_token,
            encoding_aes_key=settings.wecom_encoding_aes_key,
            corp_id=settings.wecom_corp_id,
        )
    return _crypto


@router.get("/callback")
async def verify_url(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
    crypto: WXBizMsgCrypt = Depends(get_crypto),
):
    """回调 URL 验证（企业微信后台配置回调时调用）。"""
    logger.info("=== 收到 GET 回调验证 ===")

    # 尝试 1: 使用 URL 解码后的 echostr 验证签名（官方文档标准做法）
    try:
        plaintext = crypto.verify_url(msg_signature, timestamp, nonce, echostr)
        logger.info("签名验证通过（URL解码），返回: %s", plaintext)
        return PlainTextResponse(plaintext)
    except Exception as e:
        logger.warning("签名验证失败（URL解码）: %s，尝试原始编码值...", e)

    # 尝试 2: 使用原始 URL 编码的 echostr 验证签名（部分旧版服务端行为）
    try:
        raw_params = parse_qs(request.url.query)
        echostr_encoded = raw_params.get("echostr", [None])[0]
        if echostr_encoded and echostr_encoded != echostr:
            plaintext = crypto.verify_url(msg_signature, timestamp, nonce, echostr_encoded)
            logger.info("签名验证通过（URL编码），返回: %s", plaintext)
            return PlainTextResponse(plaintext)
    except Exception as e2:
        logger.warning("签名验证失败（URL编码）: %s，尝试直接解密...", e2)

    try:
        plaintext = crypto._decrypt(echostr)
        logger.info("直接解密成功，返回: %s", plaintext)
        return PlainTextResponse(plaintext)
    except Exception as e3:
        logger.error("解密也失败: %s", e3)
        return Response(status_code=403, content="验证失败")


@router.post("/callback")
async def handle_event(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    crypto: WXBizMsgCrypt = Depends(get_crypto),
    client: WeComClient = Depends(get_wecom_client),
    settings: Settings = Depends(get_settings),
):
    """接收企业微信回调事件。"""
    body = await request.body()
    logger.info("=== 收到 POST 回调事件 ===")

    enc_match = re.search(rb"<Encrypt><!\[CDATA\[(.*?)\]\]></Encrypt>", body)
    if not enc_match:
        return Response(content="success")

    try:
        encrypted = enc_match.group(1).decode()
        plaintext = crypto.decrypt_msg(msg_signature, timestamp, nonce, encrypted)
    except Exception:
        logger.info("签名验证失败，尝试直接解密...")
        try:
            encrypted = enc_match.group(1).decode()
            plaintext = crypto._decrypt(encrypted)
        except Exception as e2:
            logger.error("事件解密失败: %s", e2)
            return Response(status_code=403, content="处理失败")

    try:
        event = parse_callback_xml(plaintext)
        logger.info("回调事件: MsgType=%s, FromUserName=%s", event.get("MsgType"), event.get("FromUserName"))

        # 文本消息 → 匹配触发词 → 回复模板卡片
        if event.get("MsgType") == "text":
            await handle_text_event(event, client, settings.wecom_agent_id)
    except Exception as e:
        logger.error("事件处理失败: %s", e)
        return Response(status_code=403, content="处理失败")

    return Response(content="success")
