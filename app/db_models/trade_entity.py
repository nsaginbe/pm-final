from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
from app.db_models.db import Base
import uuid


class Trade(Base):
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, default=lambda: f"ORD-{uuid.uuid4().hex[:8].upper()}")
    symbol = Column(String, index=True)
    action = Column(String)  # BUY, SELL, HOLD
    price = Column(Float)
    execution_price = Column(Float)
    status = Column(String)  # FILLED, SKIPPED, REJECTED
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Trade(order_id={self.order_id}, symbol={self.symbol}, action={self.action}, status={self.status})>"

