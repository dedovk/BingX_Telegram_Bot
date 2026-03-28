"""API settings service - handles BingX API key management."""
from loguru import logger

from app.bingx.client import BingXClient
from app.core.config import settings
from app.core.security import encrypt_secret, decrypt_secret
from .settings_service import SettingsService


class APISettingsService(SettingsService):
    """Handle API key validation, update, and verification - SRP focused."""

    @staticmethod
    async def check_api_connection() -> tuple[bool, str]:
        """
        Check if current API keys are valid.

        Returns:
            Tuple of (is_valid: bool, status_message: str)
        """
        client = None
        try:
            client = await APISettingsService._create_bingx_client()
            await client.get_active_spot_balance()
            return True, "Connected & Valid"
        except Exception as e:
            logger.error(f"API check failed: {e}")
            return False, "Connection Error. Check keys."
        finally:
            if client:
                await client.close_connection()

    @staticmethod
    async def validate_and_update_api_keys(new_api_key: str, new_secret_key: str) -> tuple[bool, str]:
        """
        Validate new API keys and update if valid.

        Args:
            new_api_key: New API key to validate
            new_secret_key: New secret key to validate

        Returns:
            Tuple of (success: bool, message: str)
        """
        client = None
        try:
            # Test the keys first
            client = BingXClient(api_key=new_api_key,
                                 secret_key=new_secret_key)
            await client.get_active_spot_balance()

            # If valid, encrypt and save
            encrypted_secret = encrypt_secret(
                new_secret_key, settings.ENCRYPTION_MASTER_KEY
            )

            # Update environment and settings
            APISettingsService.update_env_and_settings(
                "BINGX_API_KEY", "BINGX_API_KEY", new_api_key
            )
            APISettingsService.update_env_and_settings(
                "BINGX_SECRET_ENCRYPTED", "BINGX_SECRET_ENCRYPTED", encrypted_secret
            )

            return True, "API Keys have been updated and securely saved."

        except Exception as e:
            logger.error(f"Failed to validate/update API keys: {e}")
            return False, "The keys you provided are invalid or lack permissions. Please try again."
        finally:
            if client:
                await client.close_connection()

    @staticmethod
    async def _create_bingx_client() -> BingXClient:
        """Create BingX client with current settings."""
        clean_secret = decrypt_secret(
            settings.BINGX_SECRET_ENCRYPTED,
            settings.ENCRYPTION_MASTER_KEY
        )
        return BingXClient(
            api_key=settings.BINGX_API_KEY,
            secret_key=clean_secret
        )
