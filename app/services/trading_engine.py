import logging
from datetime import datetime
from typing import Dict, Any
from app.agents.market_monitor import MarketMonitoringAgent
from app.agents.decision_maker import DecisionMakingAgent
from app.agents.execution_agent import ExecutionAgent

logger = logging.getLogger(__name__)


class TradingEngine:
    
    def __init__(
        self,
        market_agent: MarketMonitoringAgent,
        decision_agent: DecisionMakingAgent,
        execution_agent: ExecutionAgent
    ):
        self.market_agent = market_agent
        self.decision_agent = decision_agent
        self.execution_agent = execution_agent
        self.cycle_counter = 0
    
    async def run_cycle(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Запустить один цикл торговли.
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Полный результат цикла в формате для API
        """
        self.cycle_counter += 1
        cycle_id = self.cycle_counter
        timestamp = datetime.utcnow()
        
        logs = {
            "market_agent": "",
            "decision_agent": "",
            "execution_agent": ""
        }
        
        try:
            logger.info(f"Цикл {cycle_id}: Запуск MarketMonitoringAgent")
            market_data = await self.market_agent.process(symbol)
            logs["market_agent"] = f"Received live price and calculated indicators for {symbol}"
            
            logger.info(f"Цикл {cycle_id}: Запуск DecisionMakingAgent")
            decision = await self.decision_agent.process(market_data)
            logs["decision_agent"] = (
                f"Model predicted {decision['action']} "
                f"with {decision['confidence']:.2f} confidence"
            )
            
            logger.info(f"Цикл {cycle_id}: Запуск ExecutionAgent")
            execution = await self.execution_agent.process(decision, market_data)
            if execution["executed"]:
                logs["execution_agent"] = "Trade executed successfully"
            elif execution["status"] == "SKIPPED":
                logs["execution_agent"] = "Trade skipped (HOLD action)"
            else:
                logs["execution_agent"] = f"Trade {execution['status'].lower()}"
            
            result = {
                "cycle_id": cycle_id,
                "timestamp": timestamp,
                "market_data": {
                    "symbol": market_data["symbol"],
                    "price": market_data["price"],
                    "indicators": market_data.get("features", {}),
                    "source": "binance"
                },
                "decision": {
                    "action": decision["action"],
                    "confidence": decision["confidence"],
                    "reason": decision.get("reason", "")
                },
                "execution": {
                    "executed": execution["executed"],
                    "execution_price": execution["execution_price"],
                    "order_id": execution["order_id"],
                    "status": execution["status"],
                    "time": execution["time"]
                },
                "logs": logs
            }
            
            logger.info(f"Цикл {cycle_id} завершен успешно")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка в цикле {cycle_id}: {e}")
            return {
                "cycle_id": cycle_id,
                "timestamp": timestamp,
                "market_data": {
                    "symbol": symbol,
                    "price": 0.0,
                    "indicators": {},
                    "source": "error"
                },
                "decision": {
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reason": f"Error: {str(e)}"
                },
                "execution": {
                    "executed": False,
                    "execution_price": 0.0,
                    "order_id": f"ERROR-{cycle_id}",
                    "status": "ERROR",
                    "time": timestamp
                },
                "logs": {
                    "market_agent": logs.get("market_agent", f"Error: {str(e)}"),
                    "decision_agent": "",
                    "execution_agent": ""
                }
            }

