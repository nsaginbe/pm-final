import logging
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from app.config import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    
    def __init__(self, threshold_percent: float = None):
        self.threshold_percent = threshold_percent or settings.MODEL_THRESHOLD_PERCENT
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
    
    def _prepare_features(self, klines: list) -> pd.DataFrame:
        if not klines:
            return pd.DataFrame()
        
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['sma_10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.inf)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['price_change'] = df['close'].pct_change() * 100
        
        feature_cols = ['sma_10', 'sma_50', 'rsi', 'price_change', 'volume']
        features_df = df[feature_cols].fillna(0)
        
        return features_df
    
    def _create_targets(self, features_df: pd.DataFrame) -> np.ndarray:
        targets = []
        
        hold_threshold = self.threshold_percent * 0.5
        
        for i in range(len(features_df) - 1):
            current_price = features_df.iloc[i]['sma_10']
            next_price = features_df.iloc[i + 1]['sma_10']
            
            if current_price == 0:
                targets.append(2)
                continue
            
            price_change_pct = ((next_price - current_price) / current_price) * 100
            
            if price_change_pct > self.threshold_percent:
                targets.append(0)
            elif price_change_pct < -self.threshold_percent:
                targets.append(1)
            else:
                targets.append(2)
        
        targets.append(2)
        
        unique, counts = np.unique(targets, return_counts=True)
        class_distribution = dict(zip(unique, counts))
        logger.info(f"Распределение классов в таргетах: {class_distribution}")
        
        if len(class_distribution) < 3:
            logger.warning("Не все классы представлены в таргетах. Выполняем перебалансировку.")
            price_changes = features_df['price_change'].abs().values
            hold_indices = np.argsort(price_changes)[:max(1, len(price_changes) // 5)]
            for idx in hold_indices:
                if idx < len(targets):
                    targets[idx] = 2
        
        return np.array(targets)
    
    def train_model(self, klines: list) -> Tuple[RandomForestClassifier, StandardScaler]:
        """
        Обучить модель на исторических данных.
        
        Args:
            klines: Список свечей от Binance
            
        Returns:
            Кортеж (модель, scaler)
        """
        logger.info("Начало обучения модели...")
        
        features_df = self._prepare_features(klines)
        
        if len(features_df) < 20:
            logger.warning("Недостаточно данных для обучения, используем простую модель")
            self.model = RandomForestClassifier(n_estimators=10, random_state=42)
            self.scaler = StandardScaler()
            X_synthetic = np.random.randn(60, 5)
            y_synthetic = np.array([0] * 20 + [1] * 20 + [2] * 20)
            X_scaled = self.scaler.fit_transform(X_synthetic)
            self.model.fit(X_scaled, y_synthetic)
            logger.info(f"Синтетическая модель обучена на классах: {self.model.classes_}")
            return self.model, self.scaler
        
        targets = self._create_targets(features_df)
        
        unique_classes = np.unique(targets)
        logger.info(f"Найдены классы в данных: {unique_classes}")
        
        if len(unique_classes) < 3:
            logger.warning(f"Недостаточно классов в данных. Найдено: {unique_classes}. Добавляем примеры HOLD.")
            hold_indices = []
            for i in range(min(10, len(features_df))):
                if abs(features_df.iloc[i]['price_change']) < 0.1:
                    hold_indices.append(i)
            
            if len(hold_indices) == 0:
                for i in range(max(0, len(features_df) - 5), len(features_df)):
                    if i < len(targets):
                        targets[i] = 2
        
        feature_cols = ['sma_10', 'sma_50', 'rsi', 'price_change', 'volume']
        X = features_df[feature_cols].values
        y = targets
        
        unique_y = np.unique(y)
        if len(unique_y) < 3:
            logger.warning(f"Все еще недостаточно классов: {unique_y}. Принудительно добавляем HOLD.")
            for i in range(max(0, len(y) - 3), len(y)):
                y[i] = 2
        
        if len(X) > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=None
            )
        else:
            X_train, y_train = X, y
            X_test, y_test = X, y
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test) if len(X_test) > 0 else X_train_scaled
        
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        self.model.fit(X_train_scaled, y_train)
        
        model_classes = self.model.classes_
        logger.info(f"Модель обучена на классах: {model_classes}")
        
        if len(model_classes) < 3:
            logger.error(f"Модель обучена только на {len(model_classes)} классах! Это вызовет ошибки.")
            y_train_balanced = np.copy(y_train)
            if 0 not in y_train_balanced:
                y_train_balanced[0] = 0
            if 1 not in y_train_balanced:
                y_train_balanced[min(1, len(y_train_balanced)-1)] = 1
            if 2 not in y_train_balanced:
                y_train_balanced[-1] = 2
            self.model.fit(X_train_scaled, y_train_balanced)
            model_classes = self.model.classes_
            logger.info(f"Переобучена модель на классах: {model_classes}")
        
        if len(X_test) > 0:
            score = self.model.score(X_test_scaled, y_test)
            logger.info(f"Точность модели на тестовой выборке: {score:.2f}")
        
        logger.info("Модель обучена успешно")
        return self.model, self.scaler
    
    def load_model(self, model_path: str) -> Tuple[RandomForestClassifier, StandardScaler]:
        """Загрузить сохраненную модель."""
        logger.info(f"Загрузка модели из {model_path}")
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
        
        # Проверяем количество классов в загруженной модели
        model_classes = self.model.classes_
        logger.info(f"Загруженная модель имеет классы: {model_classes}")
        
        if len(model_classes) < 3:
            logger.warning(f"Загруженная модель имеет только {len(model_classes)} классов. Рекомендуется переобучить модель.")
        
        logger.info("Модель загружена успешно")
        return self.model, self.scaler
    
    def save_model(self, model_path: str):
        """Сохранить модель."""
        if self.model is None or self.scaler is None:
            raise ValueError("Модель не обучена")
        
        logger.info(f"Сохранение модели в {model_path}")
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
        
        logger.info("Модель сохранена успешно")

