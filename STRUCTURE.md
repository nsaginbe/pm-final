Ты выступаешь как senior backend + ML инженер на Python.
Нужно реализовать backend для учебного проекта по теме:

"Coordination and Communication Protocols for Multi-Agent Financial AI Systems in Automated Trading"

Фронтендом будет заниматься другой разработчик (Flutter). Твоя задача: полностью реализовать backend-часть, архитектуру мультиагентной системы, интеграцию с Binance и API для фронтенда.

Общие требования проекта

Система должна моделировать автоматическую торговлю в виде мультиагентной архитектуры.

Обязательные три агента:

Market Monitoring Agent

Decision-Making Agent

Execution Agent

Обязательно:

Явное взаимодействие агентов (данные передаются последовательно или через общий координирующий сервис).

Понятный decision flow: мониторинг → решение → исполнение.

Использование реальных рыночных данных (Binance public API).

Использование AI-модели, а не простых if price_change > threshold.

Технологии и стек

Язык: Python

Web-фреймворк: FastAPI

HTTP-клиент: httpx (желательно async)

ML: можно использовать scikit-learn, numpy, pandas

Внешний источник данных: Binance public REST API (без ключей, только публичные эндпойнты).

БД (для хранения сделок): можно использовать SQLite (через SQLAlchemy или простой слой поверх sqlite3).

Логика мультиагентной системы
1. Market Monitoring Agent

Класс: MarketMonitoringAgent

Функции/ответственность:

Получать текущую цену инструмента, например BTCUSDT, через Binance:

GET /api/v3/ticker/price?symbol=BTCUSDT

Получать исторические свечи:

GET /api/v3/klines?symbol=BTCUSDT&interval=1m&limit=100

На основе данных по свечам считать простые индикаторы/фичи, например:

SMA (simple moving average) 10 и 50

Простой RSI или другие базовые фичи

Возвращать структурированные данные в виде словаря с полями:

symbol

price

features (словарь индикаторов)

raw_klines (по необходимости)

Использует обёртку BinanceMarketDataClient.

2. Decision-Making Agent

Класс: DecisionMakingAgent

Функции/ответственность:

Принимать на вход данные от MarketMonitoringAgent: features, price и т.п.

Использовать AI-модель (не просто if-else) для решения BUY / SELL / HOLD.

Требования к AI-модели:

Реализовать простой пайплайн, например:

Загрузить исторические свечи с Binance.

Сгенерировать из них фичи (например, дельта цены, SMA, и т.д.).

Сформировать простые псевдо-таргеты:

если следующая цена выше текущей больше чем на X% → BUY

если ниже на X% → SELL

иначе → HOLD

Обучить простую модель классификации (например, LogisticRegression или RandomForestClassifier из scikit-learn).

Обучение можно делать:

либо один раз при старте приложения (инициализация в model_loader.py),

либо вынести в отдельную функцию/скрипт, а в рантайме использовать уже обученную модель (сериализованную через pickle/joblib).

Интерфейс вызова модели оформить в модуле ml/model_inference.py, например:

def predict_action(features: Dict) -> Dict:
    return {
        "action": "BUY" | "SELL" | "HOLD",
        "confidence": float,
        "reason": str
    }


DecisionMakingAgent должен возвращать словарь вида:

{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.82,
    "reason": "Price above SMA_50, positive 1m trend",
    "model_version": "v1.0"
}

3. Execution Agent

Класс: ExecutionAgent

Функции/ответственность:

Получать решение от Decision-Making Agent: action, price.

Не выполнять реальные сделки на Binance.
В рамках учебного проекта — симуляция:

генерируется order_id (UUID),

статус сделки FILLED, SKIPPED, REJECTED и т.п. в зависимости от действия.

Записывать информацию о сделке в хранилище (например, SQLite):

symbol

action

price

execution_price

timestamp

status

Возвращать данные, пригодные для фронтенда, например:

{
    "executed": True,
    "execution_price": 43212.0,
    "order_id": "ORD-...",
    "status": "FILLED",
    "time": "2025-11-29T14:32:11Z"
}

Координация агентов

Нужен класс TradingEngine, который:

В конструкторе принимает:

MarketMonitoringAgent

DecisionMakingAgent

ExecutionAgent

Имеет метод run_cycle(symbol: str = "BTCUSDT"), который:

Запускает MarketMonitoringAgent → получает текущие данные и фичи.

Передает результат в Decision-Making Agent → получает решение.

Передает решение и цену в Execution Agent → получает результат исполнения.

Собирает единый результат цикла в структуру, пригодную для отдачи во фронтенд.

Структура ответа run_cycle должна быть такой (или максимально близкой):

{
  "cycle_id": 17,
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
    "model_version": "v1.0.3",
    "reason": "Price above SMA_50, positive trend detected"
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

API для фронтенда (FastAPI)

Нужно реализовать HTTP API, которое будет использовать Flutter-фронтенд. Минимальный набор:

POST /trading/run-cycle

Параметры:

symbol: str = "BTCUSDT" (можно query или body).

Действие:

Запускает один цикл: MarketMonitoring → DecisionMaking → Execution.

Ответ:

JSON в формате, описанном выше (cycle_id, timestamp, market_data, decision, execution, logs).

Описать Pydantic-схемы в db_models/schemas.py.

(Опционально) GET /trades

Возвращает список последних симулированных сделок.

Нужен Pydantic-модель для элемента трейда.

(Опционально) GET /market/latest

Возвращает текущие данные рынка по выбранному символу.

Требования к API:

Использовать FastAPI.

Использовать Pydantic-модели с type hints.

Валидация и понятные типы.

Ошибки (например, недоступен Binance API) оборачивать в аккуратные HTTP-ответы.

Рабочие моменты

Binance API

Используем только public endpoints, без API ключа.

Сейчас достаточно:

/api/v3/ticker/price

/api/v3/klines

Нужна обёртка BinanceMarketDataClient в services/market_data_client.py:

async функции get_current_price(symbol: str) -> float

async функции get_recent_klines(symbol: str, interval: str, limit: int) -> List[...]

Ошибки и устойчивость

Обрабатывать сетевые ошибки (timeout, HTTP error).

Если данные недоступны, возвращать понятную ошибку в API и/или заглушку.

Логирование

Добавить базовое логирование действий агентов.

Логи каждого цикла передавать в поле logs для фронтенда.

Типизация

Везде использовать аннотации типов (typing).

Поддерживать чистую архитектуру: агенты не должны напрямую знать про FastAPI.

Тесты (минимальные)

Написать хотя бы 1–2 теста:

на TradingEngine.run_cycle с заглушкой Binance клиента (mock),

проверить, что структура результата соответствует ожиданиям.

Архитектура проекта

В конце этого промпта будет приведена структура файлов проекта, которой нужно придерживаться.
Нужно:

реализовать описанные выше классы и модули в соответствии с этой структурой;

при необходимости можно немного расширить структуру (например, добавить utils/, logging.py), но не ломая основной каркас.

Ниже будет вставлена структура проекта, по которой нужно разложить код.

project_root/
  app/
    main.py                 # входная точка FastAPI
    config.py               # настройки (ключи, URL, символы и т.п.)

    api/
      routes_trading.py     # эндпойнты для фронта

    agents/
      base.py               # базовый класс агента (интерфейс)
      market_monitor.py     # MarketMonitoringAgent
      decision_maker.py     # DecisionMakingAgent
      execution_agent.py    # ExecutionAgent

    services/
      market_data_client.py # обёртка над Binance API
      trading_engine.py     # координация: мониторинг → решение → исполнение

    ml/
      model_loader.py       # загрузка/инициализация модели
      model_inference.py    # функции предсказания BUY/SELL/HOLD

    db_models/
      schemas.py            # Pydantic-схемы для API (JSON, который отдаём фронту)
      trade_entity.py       # модель трейда (для БД/хранения)
      db.py                 # подключение к БД (SQLite/Postgres)

  tests/
    test_trading_flow.py

  requirements.txt
  README.md
