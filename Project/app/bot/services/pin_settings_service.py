"""PIN settings service - handles PIN management."""
from loguru import logger

from app.core.security import hash_pin, verify_pin
from app.core.config import settings
from .settings_service import SettingsService


class PINSettingsService(SettingsService):
    """Handle PIN validation and updates - SRP focused."""

    @staticmethod
    def verify_current_pin(entered_pin: str) -> bool:
        """
        Verify if entered PIN matches the stored hash.

        Args:
            entered_pin: PIN code entered by user

        Returns:
            True if PIN is valid, False otherwise
        """
        return verify_pin(entered_pin, settings.PIN_HASH)

    @staticmethod
    def validate_pin_format(pin: str) -> tuple[bool, str]:
        """
        Validate PIN format (4-6 digits).

        Args:
            pin: PIN code to validate

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not pin.isdigit():
            return False, "Pin must contain only numbers."

        if not (4 <= len(pin) <= 6):
            return False, "Pin must be between 4 and 6 characters."

        return True, ""

    @staticmethod
    def update_pin(new_pin: str) -> tuple[bool, str]:
        """
        Hash new PIN and update .env and settings.

        Args:
            new_pin: New PIN code

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Validate format first
            is_valid, error_msg = PINSettingsService.validate_pin_format(
                new_pin)
            if not is_valid:
                return False, error_msg

            # Hash and save
            hashed_new_pin = hash_pin(new_pin)
            PINSettingsService.update_env_and_settings(
                "PIN_HASH", "PIN_HASH", hashed_new_pin
            )

            return True, "Your PIN has been securely updated."

        except Exception as e:
            logger.error(f"Failed to update PIN: {e}")
            return False, "Could not save the new PIN."
