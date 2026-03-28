"""BingX client manager - handles client lifecycle and caching."""
from loguru import logger
from app.bingx.client import BingXClient
from app.bingx.factory import BingXClientFactory
from app.core.config import settings


class BingXClientManager:
    """Manage BingX client lifecycle with caching and mode tracking."""

    _instance = None

    def __init__(self):
        """Initialize the client manager."""
        self._client: BingXClient | None = None
        self._last_mode: str = ""

    @classmethod
    def get_instance(cls) -> "BingXClientManager":
        """
        Get singleton instance of the client manager.

        Returns:
            BingXClientManager: Singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self) -> BingXClient:
        """
        Get BingX client. Creates new if trading mode changed or client doesn't exist.

        Returns:
            BingXClient: Cached or newly created client instance

        Raises:
            ValueError: If credentials are not configured
        """
        current_mode = settings.TRADING_MODE.lower()

        # Check if mode changed or client doesn't exist
        if self._client is None or self._last_mode != current_mode:
            mode_display = "Sandbox" if current_mode == "sandbox" else "Live"
            logger.info(f"Creating BingX client for {mode_display} mode")

            # Create new client
            self._client = BingXClientFactory.create()
            self._last_mode = current_mode

            logger.debug(f"Client cached for mode: {mode_display}")

        return self._client

    def reset_client(self) -> None:
        """
        Reset cached client. Used when trading mode changes.
        Next call to get_client() will create a new instance.
        """
        if self._client is not None:
            logger.debug("Resetting BingX client cache")
            self._client = None
            self._last_mode = ""

    def is_client_valid(self) -> bool:
        """
        Check if cached client is valid for current mode.

        Returns:
            bool: True if client exists and mode hasn't changed
        """
        if self._client is None:
            return False

        current_mode = settings.TRADING_MODE.lower()
        return self._last_mode == current_mode

    def get_current_mode(self) -> str:
        """
        Get the mode of the currently cached client.

        Returns:
            str: Current cached mode or empty string if no client
        """
        return self._last_mode
