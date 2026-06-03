from __future__ import annotations

from pydantic import BaseModel


class WeComApiResponse(BaseModel):
    errcode: int = 0
    errmsg: str = "ok"
    invaliduser: str | None = None
    invalidparty: str | None = None
    invalidtag: str | None = None
    unlicenseduser: str | None = None
    msgid: str | None = None
    response_code: str | None = None
