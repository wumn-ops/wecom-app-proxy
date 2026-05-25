import logging
import time

from app.models.template_card import SendTemplateCardRequest
from app.services.wecom_client import WeComClient

logger = logging.getLogger(__name__)

# 触发词 → 卡片模板定义
_TRIGGER_TEMPLATES = {
    "测试卡片": {
        "card_type": "button_interaction",
        "main_title": {"title": "项目审批通知", "desc": "您有一个新的项目立项申请需要审批"},
        "sub_title_text": "请尽快处理，超过24小时将自动驳回",
        "horizontal_content_list": [
            {"keyname": "申请人", "value": "张三"},
            {"keyname": "项目名称", "value": "企业微信集成项目"},
            {"keyname": "预算金额", "value": "500,000 元"},
        ],
        "button_list": [
            {"text": "同意", "style": 1, "type": 1, "url": "https://doc.weixin.qq.com/smartsheet/s3_AKQAYBR4AEUCNb4J9jXjKQl0gqF48_a?scode=AAkAPQcTAAobNJo8lUAe0AmwYPAHQ&tab=q979lj&viewId=vukaF8"},
            {"text": "驳回", "style": 2, "key": "reject"},
        ],
    },
}


async def handle_text_event(event: dict, client: WeComClient, agent_id: int):
    """处理文本消息事件，匹配触发词并回复模板卡片。"""
    content = event.get("Content", "").strip()
    from_user = event.get("FromUserName", "")

    if not content or not from_user:
        return

    template = _TRIGGER_TEMPLATES.get(content)
    if not template:
        logger.info("未匹配触发词: %s", content)
        return

    logger.info("匹配触发词 '%s'，向 %s 发送卡片", content, from_user)

    # 动态生成唯一 task_id，避免 button_interaction 卡片重复使用错误
    card = dict(template)
    card["task_id"] = f"task_{int(time.time() * 1000)}"

    req = SendTemplateCardRequest(
        touser=from_user,
        template_card=card,
    )
    resp = await client.send_template_card(req, agentid=agent_id)
    logger.info("卡片发送结果: errcode=%s, errmsg=%s, msgid=%s", resp.errcode, resp.errmsg, resp.msgid)
