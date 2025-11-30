# Multi-Agent Financial AI Trading System

Backend для мультиагентной системы автоматической торговли с использованием AI-моделей.

## Описание

Система моделирует автоматическую торговлю через три специализированных агента:

1. **Market Monitoring Agent** - мониторинг рынка и расчет технических индикаторов
2. **Decision-Making Agent** - принятие решений на основе ML-модели
3. **Execution Agent** - симуляция исполнения сделок

## Технологии

- **Python 3.10+**
- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **SQLite** - база данных
- **scikit-learn** - ML модели
- **httpx** - асинхронный HTTP клиент
- **Binance API** - источник рыночных данных

## Установка

1. Клонируйте репозиторий или создайте проект

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. (Опционально) Создайте файл `.env` для настройки:
```env
BINANCE_BASE_URL=https://api.binance.com
DEFAULT_SYMBOL=BTCUSDT
MODEL_PATH=./models/trading_model.pkl
DATABASE_URL=sqlite:///./trading.db
LOG_LEVEL=INFO
```

## Запуск

Запустите сервер:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступно по адресу: `http://localhost:8000`

Документация API: `http://localhost:8000/docs`

## API Endpoints

### POST `/trading/run-cycle`
Запускает один цикл торговли (мониторинг → решение → исполнение).

**Параметры:**
- `symbol` (query, optional): Торговая пара (по умолчанию: BTCUSDT)

**Ответ:**
```json
{
  "cycle_id": 1,
  "timestamp": "2025-11-29T14:32:10Z",
  "market_data": {
    "symbol": "BTCUSDT",
    "price": 43210.55,
    "indicators": {
      "sma_10": 43100.12,
      "sma_50": 42050.44,
      "rsi_14": 62.4
    },
    "source": "binance"
  },
  "decision": {
    "action": "BUY",
    "confidence": 0.84,
    "model_version": "v1.0",
    "reason": "Price above SMA_50, positive trend"
  },
  "execution": {
    "executed": true,
    "execution_price": 43212.00,
    "order_id": "ORD-20251129-987654",
    "status": "FILLED",
    "time": "2025-11-29T14:32:11Z"
  },
  "logs": {
    "market_agent": "Received live price and calculated indicators",
    "decision_agent": "Model predicted BUY with 0.84 confidence",
    "execution_agent": "Trade executed successfully"
  }
}
```

### GET `/trading/trades`
Возвращает список последних сделок.

**Параметры:**
- `limit` (query, optional): Количество трейдов (по умолчанию: 50, максимум: 100)

### GET `/trading/market/latest`
Возвращает последние данные рынка.

**Параметры:**
- `symbol` (query, optional): Торговая пара (по умолчанию: BTCUSDT)

## Архитектура

```
app/
├── main.py                 # Точка входа FastAPI
├── config.py               # Конфигурация
├── api/
│   └── routes_trading.py  # API endpoints
├── agents/
│   ├── base.py            # Базовый класс агента
│   ├── market_monitor.py  # Market Monitoring Agent
│   ├── decision_maker.py  # Decision-Making Agent
│   └── execution_agent.py # Execution Agent
├── services/
│   ├── market_data_client.py # Binance API клиент
│   └── trading_engine.py    # Координация агентов
├── ml/
│   ├── model_loader.py    # Загрузка/обучение модели
│   └── model_inference.py # Инференс модели
└── db_models/
    ├── schemas.py         # Pydantic схемы
    ├── trade_entity.py    # Модель трейда (БД)
    └── db.py              # Подключение к БД
```

## ML Модель

Система использует RandomForestClassifier для предсказания действий:
- **BUY** - покупка
- **SELL** - продажа
- **HOLD** - удержание позиции

Модель обучается на исторических данных Binance при старте приложения. Используемые фичи:
- SMA (10, 50)
- RSI (14)
- Изменение цены
- Объем торгов

## Тестирование

Запуск тестов:
```bash
pytest tests/
```

## Примечания

- Система использует только публичные API Binance (без API ключей)
- Все сделки симулируются, реальные сделки не выполняются
- База данных SQLite создается автоматически при первом запуске
- ML модель обучается при старте приложения на исторических данных

## Лицензия

Учебный проект.

