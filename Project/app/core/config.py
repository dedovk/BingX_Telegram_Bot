from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str
    BINGX_API_KEY: str
    BINGX_SECRET_API: str

    ALLOWED_USERS_IDS: List[int]

    PIN_CODE: int

    # pydantic settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    # additional validator for the list of IDs
    @field_validator(ALLOWED_USERS_IDS, mode="before")
    @classmethod
    def parse_allowed_users(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",")]
        return v


settings = Settings()
