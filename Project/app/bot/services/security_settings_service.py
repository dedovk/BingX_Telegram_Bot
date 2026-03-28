"""Security settings service - handles 2FA/TOTP management."""
import pyotp
from loguru import logger

from app.core.config import settings
from .settings_service import SettingsService


class SecuritySettingsService(SettingsService):
    """Handle 2FA/TOTP management - SRP focused."""

    @staticmethod
    def generate_new_totp_secret() -> str:
        """
        Generate new random base32 TOTP secret.

        Returns:
            New TOTP secret string
        """
        return pyotp.random_base32()

    @staticmethod
    def update_totp_secret(new_secret: str) -> tuple[bool, str]:
        """
        Update TOTP secret in .env and settings.

        Args:
            new_secret: New TOTP secret

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            SecuritySettingsService.update_env_and_settings(
                "TOTP_SECRET", "TOTP_SECRET", new_secret
            )
            return True, new_secret
        except Exception as e:
            logger.error(f"Failed to update TOTP secret: {e}")
            return False, ""

    @staticmethod
    def reset_2fa() -> tuple[bool, str, str]:
        """
        Reset 2FA by generating new TOTP secret and updating settings.

        Returns:
            Tuple of (success: bool, error_message: str, new_secret: str)
        """
        try:
            new_secret = SecuritySettingsService.generate_new_totp_secret()
            success, _ = SecuritySettingsService.update_totp_secret(new_secret)

            if success:
                return True, "", new_secret
            else:
                return False, "Could not save new TOTP secret.", ""

        except Exception as e:
            logger.error(f"Failed to reset 2FA: {e}")
            return False, "Could not reset 2FA.", ""
