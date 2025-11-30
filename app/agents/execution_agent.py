import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agents.base import BaseAgent
from app.db_models.trade_entity import Trade

logger = logging.getLogger(__name__)


class ExecutionAgent(BaseAgent):
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_order_id(self) -> str:
        """Сгенерировать уникальный ID ордера."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"ORD-{date_str}-{unique_id}"
    
    async def process(
        self, 
        decision: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Симулировать исполнение сделки.
        
        Args:
            decision: Решение от DecisionMakingAgent
            market_data: Данные от MarketMonitoringAgent
            
        Returns:
            Словарь с результатом исполнения:
            {
                "executed": bool,
                "execution_price": float,
                "order_id": str,
                "status": str,
                "time": datetime
            }
        """
        try:
            action = decision.get("action", "HOLD")
            price = market_data.get("price", 0.0)
            symbol = market_data.get("symbol", "BTCUSDT")
            confidence = decision.get("confidence", 0.0)
            
            order_id = self._generate_order_id()
            execution_time = datetime.utcnow()
            
            if action == "HOLD":
                status = "SKIPPED"
                executed = False
                execution_price = price
            elif confidence < 0.6:
                status = "REJECTED"
                executed = False
                execution_price = price
            else:
                status = "FILLED"
                executed = True
                slippage = price * 0.0001
                execution_price = price + slippage if action == "BUY" else price - slippage
            
            trade = Trade(
                order_id=order_id,
                symbol=symbol,
                action=action,
                price=price,
                execution_price=execution_price,
                status=status,
                timestamp=execution_time
            )
            
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            result = {
                "executed": executed,
                "execution_price": execution_price,
                "order_id": order_id,
                "status": status,
                "time": execution_time
            }
            
            logger.info(
                f"ExecutionAgent: сделка {order_id} - {action} "
                f"({status}) по цене {execution_price:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в ExecutionAgent: {e}")
            self.db.rollback()
            return {
                "executed": False,
                "execution_price": market_data.get("price", 0.0),
                "order_id": f"ERROR-{uuid.uuid4().hex[:8]}",
                "status": "ERROR",
                "time": datetime.utcnow()
            }

