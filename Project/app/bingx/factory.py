"""BingX client factory - creates client instances based on trading mode."""
from loguru import logger
from app.bingx.client import BingXClient
from app.core.config import settings
from app.core.security import decrypt_secret


class BingXClientFactory:
    """Factory for creating BingX client instances."""

    @staticmethod
    def create() -> BingXClient:
        """
        Create BingX client based on current trading mode.

        Returns:
            BingXClient instance configured for current mode

        Raises:
            ValueError: If credentials are not configured
        """
        is_sandbox = settings.is_sandbox_mode()

        # Get API key
        api_key = settings.get_api_key()
        if not api_key:
            raise ValueError("API key not configured for current trading mode")

        # Get and decrypt secret
        secret_encrypted = settings.get_secret_encrypted()
        if not secret_encrypted:
            raise ValueError(
                "Secret key not configured for current trading mode")

        secret_key = decrypt_secret(
            secret_encrypted, settings.ENCRYPTION_MASTER_KEY)

        mode = "Sandbox" if is_sandbox else "Live"
        logger.info(f"Creating BingX client for {mode} mode")

        return BingXClient(
            api_key=api_key,
            secret_key=secret_key,
            is_sandbox=is_sandbox
        )

    @staticmethod
    def create_live() -> BingXClient:
        """Create client for live trading."""
        api_key = settings.BINGX_API_KEY
        secret_encrypted = settings.BINGX_SECRET_ENCRYPTED

        if not api_key or not secret_encrypted:
            raise ValueError("Live credentials not configured")

        secret_key = decrypt_secret(
            secret_encrypted, settings.ENCRYPTION_MASTER_KEY)
        return BingXClient(api_key=api_key, secret_key=secret_key, is_sandbox=False)

    @staticmethod
    def create_sandbox() -> BingXClient:
        """Create client for sandbox trading."""
        api_key = settings.BINGX_SANDBOX_API_KEY or settings.BINGX_API_KEY
        secret_encrypted = (
            settings.BINGX_SANDBOX_SECRET_ENCRYPTED
            or settings.BINGX_SECRET_ENCRYPTED
        )

        if not api_key or not secret_encrypted:
            raise ValueError("Sandbox credentials not configured")

        secret_key = decrypt_secret(
            secret_encrypted, settings.ENCRYPTION_MASTER_KEY)
        return BingXClient(api_key=api_key, secret_key=secret_key, is_sandbox=True)
