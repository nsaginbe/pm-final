import logging
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.ml.model_inference import predict_action

logger = logging.getLogger(__name__)


class DecisionMakingAgent(BaseAgent):
    
    async def process(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принять решение на основе данных рынка.
        
        Args:
            market_data: Данные от MarketMonitoringAgent
            
        Returns:
            Словарь с решением:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "confidence": float,
                "reason": str
            }
        """
        try:
            features = market_data.get("features", {})
            
            prediction = predict_action(features)
            
            logger.info(
                f"DecisionMakingAgent: решение - {prediction['action']} "
                f"(confidence: {prediction['confidence']:.2f})"
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Ошибка в DecisionMakingAgent: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "reason": f"Error in decision making: {str(e)}"
            }

