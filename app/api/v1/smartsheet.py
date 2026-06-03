import httpx
from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_settings, get_wecom_client
from app.services.wecom_client import WeComClient

router = APIRouter(prefix="/smartsheet", tags=["SmartSheet"])

SYSTEMS = ["MES", "CPS", "VPS", "其他"]


def _extract_text(val) -> str:
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
        "key_type": "CELL_VALUE_KEY_TYPE_FIELD_ID",
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

    f_status = settings.smartsheet_field_status
    f_system = settings.smartsheet_field_system
    f_verify = settings.smartsheet_field_verify

    rows = []
    pending_total = 0

    for sys_name in SYSTEMS:
        processing = 0
        waiting_pm = 0
        waiting_verify = 0

        for r in all_records:
            vals = r.get("values", {})
            system_val = _extract_text(vals.get(f_system))
            if system_val != sys_name:
                continue

            status_val = _extract_text(vals.get(f_status))
            verify_val = _extract_text(vals.get(f_verify))

            if status_val == "处理中":
                processing += 1
            elif status_val == "":
                waiting_pm += 1
            elif status_val == "已解决待验证" and verify_val == "":
                waiting_verify += 1

        rows.append({
            "system": sys_name,
            "processing": processing,
            "waiting_pm": waiting_pm,
            "waiting_verify": waiting_verify,
        })
        pending_total += processing + waiting_pm

    return {
        "pending_total": pending_total,
        "rows": rows,
    }
