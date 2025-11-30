from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MarketDataSchema(BaseModel):
    symbol: str
    price: float
    indicators: Dict[str, float] = Field(default_factory=dict)
    source: str = "binance"


class DecisionSchema(BaseModel):
    action: str  # BUY, SELL, HOLD
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class ExecutionSchema(BaseModel):
    executed: bool
    execution_price: float
    order_id: str
    status: str
    time: datetime


class LogsSchema(BaseModel):
    market_agent: str = ""
    decision_agent: str = ""
    execution_agent: str = ""


class TradingCycleResponse(BaseModel):
    cycle_id: int
    timestamp: datetime
    market_data: MarketDataSchema
    decision: DecisionSchema
    execution: ExecutionSchema
    logs: LogsSchema


class TradeResponse(BaseModel):
    id: int
    order_id: str
    symbol: str
    action: str
    price: float
    execution_price: float
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
        model_config = {"from_attributes": True}


class MarketLatestResponse(BaseModel):
    symbol: str
    price: float
    indicators: Dict[str, float]
    timestamp: datetime

