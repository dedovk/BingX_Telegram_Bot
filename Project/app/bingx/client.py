import ccxt.async_support as ccxt
from loguru import logger


class BingXClient:

    def __init__(self, api_key: str, secret_key: str):
        """initialization bingx async client"""
        self.exchange = ccxt.bingx({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}  # swap - futures / spot - spot
        })

    async def get_usdt_balance(self) -> float:
        """get account balance(usdt)"""
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

    async def close_connection(self):
        await self.exchange.close()
