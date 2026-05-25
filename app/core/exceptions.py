class WeComApiError(Exception):
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"WeChat API error [{errcode}]: {errmsg}")


class TokenRefreshError(Exception):
    pass


class WeComHttpError(Exception):
    pass
