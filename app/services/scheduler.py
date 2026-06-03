import asyncio
import logging
import time
from datetime import datetime, timedelta

from app.models.template_card import SendTemplateCardRequest
from app.services.wecom_client import WeComClient

logger = logging.getLogger(__name__)


class CronScheduler:
    """轻量 cron 定时器 — 解析 5 字段 cron 表达式，到点执行任务。"""

    def __init__(self, cron_expr: str, client: WeComClient, touser: str, agent_id: int, page_url: str):
        self._cron = self._parse(cron_expr)
        self._client = client
        self._touser = touser
        self._agent_id = agent_id
        self._page_url = page_url
        self._task: asyncio.Task | None = None

    @staticmethod
    def _parse(expr: str) -> dict:
        parts = expr.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expr}")
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "weekday": parts[4],
        }

    @staticmethod
    def _match(field: str, value: int) -> bool:
        if field == "*":
            return True
        return value in [int(x) for x in field.split(",")]

    def _next_run(self) -> datetime:
        now = datetime.now()
        dt = now.replace(second=0, microsecond=0)
        # 从下一秒开始搜索，避免当前分钟重复触发
        for _ in range(8 * 24 * 60):
            dt += timedelta(minutes=1)
            if (self._match(self._cron["minute"], dt.minute)
                    and self._match(self._cron["hour"], dt.hour)
                    and self._match(self._cron["day"], dt.day)
                    and self._match(self._cron["month"], dt.month)
                    and self._match(self._cron["weekday"], self._cron_weekday(dt))):
                return dt
        raise RuntimeError("No matching cron time in next 8 days")

    @staticmethod
    def _cron_weekday(dt: datetime) -> int:
        """datetime.isoweekday() → cron weekday."""
        w = dt.isoweekday()  # 1=Mon … 7=Sun
        return 0 if w == 7 else w

    async def _send_reminder(self):
        card = {
            "card_type": "button_interaction",
            "main_title": {"title": "生科生产域问题及需求统计"},
            "sub_title_text": "请点击下方查看按钮",
            "task_id": f"reminder_{int(time.time() * 1000)}",
            "button_list": [
                {"text": "查看", "style": 1, "type": 1, "url": self._page_url},
            ],
        }
        req = SendTemplateCardRequest(touser=self._touser, template_card=card)
        resp = await self._client.send_template_card(req, agentid=self._agent_id)
        logger.info("提醒卡片已发送: errcode=%s, msgid=%s", resp.errcode, resp.msgid)

    async def run(self):
        while True:
            next_run = self._next_run()
            wait = (next_run - datetime.now()).total_seconds()
            logger.info("下次提醒时间: %s (%.0f 分钟后)", next_run.strftime("%Y-%m-%d %H:%M"), wait / 60)
            await asyncio.sleep(wait)
            try:
                await self._send_reminder()
            except Exception:
                logger.exception("定时提醒发送失败")

    def start(self):
        self._task = asyncio.create_task(self.run())

    def stop(self):
        if self._task:
            self._task.cancel()
