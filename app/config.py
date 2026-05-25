from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
    )

    wecom_corp_id: str
    wecom_corp_secret: str
    wecom_agent_id: int = 0
    wecom_default_touser: str = ""
    wecom_token: str = ""
    wecom_encoding_aes_key: str = ""
    wecom_api_base_url: str = "https://qyapi.weixin.qq.com"
    wecom_token_refresh_buffer: int = 300
    log_level: str = "INFO"
