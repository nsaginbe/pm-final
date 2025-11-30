import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db_models.db import Base, engine
from app.api.routes_trading import router as trading_router
from app.services.market_data_client import BinanceMarketDataClient
from app.ml.model_loader import ModelLoader
from app.ml.model_inference import initialize_model
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    
    Base.metadata.create_all(bind=engine)
    logger.info("База данных инициализирована")
    
    try:
        logger.info("Инициализация ML модели...")
        model_loader = ModelLoader()
        
        if settings.MODEL_PATH:
            try:
                model_loader.load_model(settings.MODEL_PATH)
                if len(model_loader.model.classes_) < 3:
                    logger.warning("Загруженная модель имеет недостаточно классов. Переобучаем...")
                    raise ValueError("Model has insufficient classes")
                logger.info("Модель загружена из файла")
            except (FileNotFoundError, ValueError, KeyError) as e:
                logger.info(f"Модель не может быть использована ({e}), обучение новой модели...")
                market_client = BinanceMarketDataClient()
                
                klines = await market_client.get_recent_klines(
                    symbol=settings.DEFAULT_SYMBOL,
                    interval="1h",
                    limit=500
                )

                model_loader.train_model(klines)
                if settings.MODEL_PATH:
                    model_loader.save_model(settings.MODEL_PATH)
                await market_client.close()
        else:
            logger.info("Обучение модели на исторических данных...")
            market_client = BinanceMarketDataClient()
            klines = await market_client.get_recent_klines(
                symbol=settings.DEFAULT_SYMBOL,
                interval="1h",
                limit=500
            )
            model_loader.train_model(klines)
            await market_client.close()
        
        initialize_model(model_loader)
        logger.info("ML модель готова к использованию")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации модели: {e}")
        logger.warning("Продолжаем работу без модели (будут использоваться заглушки)")
    
    yield
    
    logger.info("Завершение работы приложения...")


app = FastAPI(
    title="Multi-Agent Trading System API",
    description="API для мультиагентной системы автоматической торговли",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(trading_router)


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {"status": "healthy"}

