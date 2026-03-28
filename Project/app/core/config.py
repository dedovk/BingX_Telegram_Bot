import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    BOT_TOKEN: str

    # Trading mode: "live" or "sandbox"
    TRADING_MODE: str = "live"

    # Live mode credentials
    BINGX_API_KEY: str
    BINGX_SECRET_ENCRYPTED: str

    # Sandbox mode credentials (optional - can use same as live if not provided)
    BINGX_SANDBOX_API_KEY: str = ""
    BINGX_SANDBOX_SECRET_ENCRYPTED: str = ""

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

    def get_api_key(self) -> str:
        """Get API key based on current trading mode."""
        if self.TRADING_MODE == "sandbox":
            return self.BINGX_SANDBOX_API_KEY or self.BINGX_API_KEY
        return self.BINGX_API_KEY

    def get_secret_encrypted(self) -> str:
        """Get encrypted secret based on current trading mode."""
        if self.TRADING_MODE == "sandbox":
            return self.BINGX_SANDBOX_SECRET_ENCRYPTED or self.BINGX_SECRET_ENCRYPTED
        return self.BINGX_SECRET_ENCRYPTED

    def is_sandbox_mode(self) -> bool:
        """Check if running in sandbox mode."""
        return self.TRADING_MODE.lower() == "sandbox"


settings = Settings()
