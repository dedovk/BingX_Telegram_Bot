"""Trading mode service - manage live/sandbox mode switching."""
from loguru import logger
from app.core.config import settings
from .settings_service import SettingsService


class TradingModeService(SettingsService):
    """Handle trading mode switching and validation - SRP focused."""

    @staticmethod
    def get_current_mode() -> str:
        """Get current trading mode."""
        return settings.TRADING_MODE.lower()

    @staticmethod
    def is_sandbox_mode() -> bool:
        """Check if currently in sandbox mode."""
        return settings.is_sandbox_mode()

    @staticmethod
    def get_mode_display_name() -> str:
        """Get human-readable mode name."""
        return "📦 Sandbox (Demo)" if settings.is_sandbox_mode() else "🔴 Live"

    @staticmethod
    async def switch_trading_mode(new_mode: str) -> tuple[bool, str]:
        """
        Switch between live and sandbox trading modes.
        
        Args:
            new_mode: "live" or "sandbox"
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        new_mode = new_mode.lower().strip()
        
        if new_mode not in ["live", "sandbox"]:
            return False, "Invalid mode. Use 'live' or 'sandbox'."
        
        if new_mode == settings.TRADING_MODE.lower():
            return False, f"Already in {new_mode} mode."
        
        try:
            # Update config
            TradingModeService.update_env_and_settings(
                "TRADING_MODE", "TRADING_MODE", new_mode
            )
            
            mode_display = TradingModeService.get_mode_display_name()
            logger.info(f"Trading mode switched to: {mode_display}")
            
            return True, f"Successfully switched to {mode_display} mode."
            
        except Exception as e:
            logger.error(f"Failed to switch trading mode: {e}")
            return False, "Failed to switch trading mode."

    @staticmethod
    def get_credentials_status() -> dict:
        """
        Get status of configured credentials.
        
        Returns:
            Dictionary with credentials status
        """
        return {
            "current_mode": settings.TRADING_MODE.lower(),
            "live_api_key_set": bool(settings.BINGX_API_KEY),
            "sandbox_api_key_set": bool(settings.BINGX_SANDBOX_API_KEY),
            "using_fallback": (
                settings.TRADING_MODE.lower() == "sandbox" 
                and not settings.BINGX_SANDBOX_API_KEY
            )
        }

    @staticmethod
    def get_mode_info() -> str:
        """Get detailed information about current mode."""
        status = TradingModeService.get_credentials_status()
        current = TradingModeService.get_mode_display_name()
        
        info = f"**Current Mode:** {current}\n\n"
        
        if status["using_fallback"]:
            info += "⚠️ **Using live credentials for sandbox testing**\n"
        
        info += "**Available Credentials:**\n"
        info += f"{'✅' if status['live_api_key_set'] else '❌'} Live API Key\n"
        info += f"{'✅' if status['sandbox_api_key_set'] else '❌'} Sandbox API Key\n"
        
        return info
