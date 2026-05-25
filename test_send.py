import sys
sys.path.insert(0, r"d:\Trae-space\wecom-app-proxy")

import asyncio
from app.dependencies import get_settings, get_token_manager, get_wecom_client
from app.models.template_card import SendTemplateCardRequest

async def main():
    settings = get_settings()
    print(f"Config: corp={settings.wecom_corp_id[:6]}..., agent={settings.wecom_agent_id}, user={settings.wecom_default_touser}")

    client = await get_wecom_client(settings)

    req = SendTemplateCardRequest(
        touser=settings.wecom_default_touser,
        template_card={
            "card_type": "text_notice",
            "main_title": {"title": "测试消息", "desc": "通过 wecom-app-proxy 发送的第一条模板卡片"},
            "sub_title_text": "如果你看到这条消息，说明服务运行正常!",
            "emphasis_content": {"title": "成功", "desc": "发送状态"},
            "horizontal_content_list": [
                {"keyname": "发送方", "value": "消息中心"},
                {"keyname": "类型", "value": "文本通知型"},
            ],
            "card_action": {"type": 1, "url": "https://work.weixin.qq.com"},
        },
    )

    resp = await client.send_template_card(req, agentid=settings.wecom_agent_id)
    print(f"SUCCESS: errcode={resp.errcode}, errmsg={resp.errmsg}, msgid={resp.msgid}")

asyncio.run(main())
