import logging
import pandas as pd
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.services.market_data_client import BinanceMarketDataClient

logger = logging.getLogger(__name__)


class MarketMonitoringAgent(BaseAgent):
    
    def __init__(self, market_client: BinanceMarketDataClient):
        self.market_client = market_client
    
    def _calculate_sma(self, prices: List[float], window: int) -> float:
        """Вычислить Simple Moving Average."""
        if len(prices) < window:
            return prices[-1] if prices else 0.0
        return sum(prices[-window:]) / window
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Вычислить RSI (упрощенная версия)."""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        recent_deltas = deltas[-period:]
        
        gains = [d for d in recent_deltas if d > 0]
        losses = [-d for d in recent_deltas if d < 0]
        
        avg_gain = sum(gains) / period if gains else 0.0
        avg_loss = sum(losses) / period if losses else 0.0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _extract_features_from_klines(self, klines: List[List]) -> Dict[str, float]:
        """Извлечь фичи из свечей."""
        if not klines:
            return {}
        
        closes = [float(k[4]) for k in klines]
        
        features = {
            "sma_10": self._calculate_sma(closes, 10),
            "sma_50": self._calculate_sma(closes, 50),
            "rsi_14": self._calculate_rsi(closes, 14),
            "current_price": closes[-1],
            "price_change_1m": (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0.0,
        }
        
        return features
    
    async def process(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Получить данные рынка и рассчитать индикаторы.
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Словарь с данными рынка и фичами
        """
        try:
            current_price = await self.market_client.get_current_price(symbol)
            
            klines = await self.market_client.get_recent_klines(
                symbol=symbol,
                interval="1m",
                limit=100
            )
            
            features = self._extract_features_from_klines(klines)
            
            result = {
                "symbol": symbol,
                "price": current_price,
                "features": features,
                "raw_klines": klines[:10] if klines else []
            }
            
            logger.info(f"MarketMonitoringAgent: получены данные для {symbol}, цена: {current_price}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в MarketMonitoringAgent: {e}")
            raise

