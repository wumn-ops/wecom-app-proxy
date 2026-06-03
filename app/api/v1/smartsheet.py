import httpx
from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_settings, get_wecom_client
from app.services.wecom_client import WeComClient

router = APIRouter(prefix="/smartsheet", tags=["SmartSheet"])


def _extract_text(val) -> str:
    """提取字段的文本值。"""
    if val is None:
        return ""
    if isinstance(val, list) and len(val) > 0:
        item = val[0]
        if isinstance(item, dict):
            return item.get("text", "")
    if isinstance(val, str):
        return val
    return ""


@router.get("/stats")
async def smartsheet_stats(
    settings: Settings = Depends(get_settings),
    client: WeComClient = Depends(get_wecom_client),
):
    token = await client._token_manager.get_token()
    base_payload = {
        "docid": settings.smartsheet_docid,
        "sheet_id": settings.smartsheet_sheet_id,
        "key_type": "CELL_VALUE_KEY_TYPE_FIELD_TITLE",
        "limit": 1000,
    }

    all_records = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as http:
        offset = 0
        while True:
            payload = {**base_payload, "offset": offset}
            resp = await http.post(
                f"https://qyapi.weixin.qq.com/cgi-bin/wedoc/smartsheet/get_records?access_token={token}",
                json=payload,
            )
            data = resp.json()
            all_records.extend(data.get("records", []))
            if not data.get("has_more"):
                break
            offset = data.get("next", 0)

    total = len(all_records)
    status_field = settings.smartsheet_status_field

    # 统计各状态数量
    status_counts: dict[str, int] = {}
    not_passed = 0
    for r in all_records:
        status = _extract_text(r.get("values", {}).get(status_field))
        if not status:
            status = "未填写"
        status_counts[status] = status_counts.get(status, 0) + 1
        if status != "通过":
            not_passed += 1

    items = []
    for r in all_records:
        vals = r.get("values", {})
        items.append({
            "record_id": r["record_id"],
            "content": _extract_text(vals.get("需求内容-机器人")),
            "system": _extract_text(vals.get("所属系统-机器人")),
            "status": _extract_text(vals.get(status_field)) or "未填写",
            "creator": _extract_text(vals.get("需求人提出姓名-机器人")),
            "update_time": r.get("update_time", ""),
        })

    return {
        "total": total,
        "not_passed": not_passed,
        "passed": total - not_passed,
        "status_counts": status_counts,
        "items": items,
    }
