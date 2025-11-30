from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    # Binance API
    BINANCE_BASE_URL: str = "https://api.binance.com"
    
    # Торговые параметры
    DEFAULT_SYMBOL: str = "BTCUSDT"
    DEFAULT_INTERVAL: str = "1m"
    DEFAULT_KLINES_LIMIT: int = 100
    
    # ML Model
    MODEL_THRESHOLD_PERCENT: float = 0.5
    MODEL_PATH: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///./trading.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()

