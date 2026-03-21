import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    BOT_TOKEN: str
    BINGX_API_KEY: str

    BINGX_SECRET_ENCRYPTED: str
    ENCRYPTION_MASTER_KEY: str

    ALLOWED_USERS_IDS: List[int]

    TOTP_SECRET: str

    PIN_HASH: str

    # pydantic settings
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # additional validator for the list of IDs
    @field_validator("ALLOWED_USERS_IDS", mode="before")
    @classmethod
    def parse_allowed_users(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",")]
        elif isinstance(v, int):
            return [v]
        return v


settings = Settings()
