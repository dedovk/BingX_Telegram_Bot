"""Base settings service with common operations."""
import dotenv
from loguru import logger
from app.core.config import settings


class SettingsService:
    """Base service for settings management - follows SRP and DIP."""

    @staticmethod
    def update_env_variable(key: str, value: str) -> None:
        """
        Update environment variable in .env file.
        
        Args:
            key: Environment variable name
            value: New value
            
        Raises:
            Exception: If .env update fails
        """
        try:
            dotenv.set_key(".env", key, value)
            logger.debug(f"Environment variable {key} updated")
        except Exception as e:
            logger.error(f"Failed to update {key} in .env: {e}")
            raise

    @staticmethod
    def update_settings_attribute(key: str, value: str) -> None:
        """
        Update settings object attribute.
        
        Args:
            key: Attribute name
            value: New value
        """
        setattr(settings, key, value)
        logger.debug(f"Settings attribute {key} updated")

    @staticmethod
    def update_env_and_settings(env_key: str, setting_key: str, value: str) -> None:
        """
        Update both .env file and settings object (DRY principle).
        
        Args:
            env_key: Environment variable name
            setting_key: Settings attribute name
            value: New value
        """
        SettingsService.update_env_variable(env_key, value)
        SettingsService.update_settings_attribute(setting_key, value)

    @staticmethod
    def log_user_action(user_id: int, username: str, action: str) -> None:
        """Log user action with consistent format."""
        logger.info(f"User(ID: {user_id}, Username: {username}) {action}")

    @staticmethod
    def log_user_warning(user_id: int, username: str, action: str) -> None:
        """Log user warning with consistent format."""
        logger.warning(f"User(ID: {user_id}, Username: {username}) {action}")

    @staticmethod
    def log_user_error(user_id: int, username: str, action: str, error: Exception = None) -> None:
        """Log user error with consistent format."""
        error_msg = f" {error}" if error else ""
        logger.error(f"User(ID: {user_id}, Username: {username}) {action}:{error_msg}")

    @staticmethod
    def log_user_success(user_id: int, username: str, action: str) -> None:
        """Log successful user action."""
        logger.success(f"User(ID: {user_id}, Username: {username}) {action}")
