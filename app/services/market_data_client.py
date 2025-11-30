import httpx
import logging
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class BinanceMarketDataClient:
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.BINANCE_BASE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Получить текущую цену инструмента.
        
        Args:
            symbol: Торговая пара (например, BTCUSDT)
            
        Returns:
            Текущая цена
            
        Raises:
            httpx.HTTPError: При ошибке запроса
        """
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {"symbol": symbol}
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            price = float(data["price"])
            logger.info(f"Получена цена {symbol}: {price}")
            return price
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при получении цены {symbol}: {e}")
            raise
    
    async def get_recent_klines(
        self, 
        symbol: str, 
        interval: str = "1m", 
        limit: int = 100
    ) -> List[List[Any]]:
        """
        Получить исторические свечи.
        
        Args:
            symbol: Торговая пара
            interval: Интервал (1m, 5m, 1h и т.д.)
            limit: Количество свечей
            
        Returns:
            Список свечей в формате Binance:
            [
                [open_time, open, high, low, close, volume, ...],
                ...
            ]
            
        Raises:
            httpx.HTTPError: При ошибке запроса
        """
        url = f"{self.base_url}/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            klines = response.json()
            logger.info(f"Получено {len(klines)} свечей для {symbol}")
            return klines
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при получении свечей {symbol}: {e}")
            raise
    
    async def close(self):
        """Закрыть HTTP клиент."""
        await self.client.aclose()

