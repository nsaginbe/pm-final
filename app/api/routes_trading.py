from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.db_models.schemas import (
    TradingCycleResponse,
    TradeResponse,
    MarketLatestResponse
)
from app.db_models.db import get_db
from app.db_models.trade_entity import Trade
from app.services.trading_engine import TradingEngine
from app.services.market_data_client import BinanceMarketDataClient
from app.agents.market_monitor import MarketMonitoringAgent
from app.agents.decision_maker import DecisionMakingAgent
from app.agents.execution_agent import ExecutionAgent
from app.config import settings
from datetime import datetime

router = APIRouter(prefix="/trading", tags=["trading"])


def get_trading_engine(db: Session = Depends(get_db)) -> TradingEngine:
    market_client = BinanceMarketDataClient()
    market_agent = MarketMonitoringAgent(market_client)
    decision_agent = DecisionMakingAgent()
    execution_agent = ExecutionAgent(db)
    
    return TradingEngine(
        market_agent=market_agent,
        decision_agent=decision_agent,
        execution_agent=execution_agent
    )


@router.post("/run-cycle", response_model=TradingCycleResponse)
async def run_trading_cycle(
    symbol: str = Query(default="BTCUSDT", description="Торговая пара"),
    engine: TradingEngine = Depends(get_trading_engine)
):
    """
    Запустить один цикл торговли.
    
    Цикл включает:
    1. Мониторинг рынка (получение данных и индикаторов)
    2. Принятие решения (ML модель)
    3. Исполнение сделки (симуляция)
    """
    try:
        result = await engine.run_cycle(symbol=symbol)
        return TradingCycleResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения цикла: {str(e)}")


@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    limit: int = Query(default=50, ge=1, le=100, description="Количество трейдов"),
    db: Session = Depends(get_db)
):
    """Получить список последних сделок."""
    trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
    return [TradeResponse.model_validate(trade) for trade in trades]


@router.get("/market/latest", response_model=MarketLatestResponse)
async def get_market_latest(
    symbol: str = Query(default="BTCUSDT", description="Торговая пара")
):
    """Получить последние данные рынка."""
    try:
        market_client = BinanceMarketDataClient()
        market_agent = MarketMonitoringAgent(market_client)
        
        market_data = await market_agent.process(symbol)
        
        return MarketLatestResponse(
            symbol=market_data["symbol"],
            price=market_data["price"],
            indicators=market_data.get("features", {}),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных рынка: {str(e)}")

