import ccxt.async_support as ccxt

from loguru import logger
from app.bingx.models import SpotBalance


class BingXClient:

    def __init__(self, api_key: str, secret_key: str, is_sandbox: bool = False):
        """
        Initialize BingX async client.

        Args:
            api_key: BingX API key
            secret_key: BingX secret key
            is_sandbox: If True, use sandbox/demo trading mode
        """
        self.is_sandbox = is_sandbox
        self.exchange = ccxt.bingx({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},  # swap - futures / spot - spot
            'sandbox': is_sandbox  # Enable sandbox mode if needed
        })

        mode = "Sandbox" if is_sandbox else "Live"
        logger.info(f"BingX client initialized in {mode} mode")

    async def get_usdt_balance(self) -> float:
        """get account balance(usdt futures)"""
        try:
            logger.info("Request balance from BingX.")

            balance = await self.exchange.fetch_balance()

            usdt_free = balance.get("USDT", {}).get('free', 0.0)

            logger.success(f"Got balance succesfully: {usdt_free} USDT")
            return float(usdt_free)

        except ccxt.AuthenticationError as e:
            logger.error(f"BingX Authorization error: {e}")
            raise e
        except Exception as e:
            logger.exception(f"BingX balance retrieval error: {e}")
            raise e

    async def get_active_spot_balance(self) -> list[SpotBalance]:
        """get spot balance"""
        try:
            logger.info("Request spot balance from BingX")

            raw_balances = await self.exchange.fetch_balance({'type': 'spot'})

            active_balances = []

            for asset, data in raw_balances.items():
                if asset in ['info', 'free', "used", 'total'] or not isinstance(data, dict):
                    continue

                free = float(data.get('free', 0.0))
                locked = float(data.get('used', 0.0))

                if free + locked > 0:
                    active_balances.append(
                        SpotBalance(asset=asset, free=free, locked=locked)
                    )

            logger.success(f"Got {len(active_balances)} active spot assets.")
            return active_balances

        except Exception as e:
            logger.exception(f" BingX spot balance retrieval error: {e}")
            raise e

    async def close_connection(self):
        await self.exchange.close()
