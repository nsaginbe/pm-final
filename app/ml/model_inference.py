import logging
import numpy as np
from typing import Dict, Any
from app.ml.model_loader import ModelLoader

logger = logging.getLogger(__name__)

_model_loader: ModelLoader = None


def initialize_model(model_loader: ModelLoader):
    global _model_loader
    _model_loader = model_loader


def predict_action(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Предсказать действие на основе фичей.
    
    Args:
        features: Словарь с фичами (sma_10, sma_50, rsi_14, price_change_1m, current_price)
        
    Returns:
        Словарь с предсказанием:
        {
            "action": "BUY" | "SELL" | "HOLD",
            "confidence": float,
            "reason": str
        }
    """
    global _model_loader
    
    if _model_loader is None or _model_loader.model is None:
        logger.warning("Модель не инициализирована, возвращаем HOLD")
        return {
            "action": "HOLD",
            "confidence": 0.5,
            "reason": "Model not initialized"
        }
    
    try:
        feature_order = ['sma_10', 'sma_50', 'rsi', 'price_change', 'volume']
        
        feature_array = []
        for feat_name in feature_order:
            if feat_name == 'price_change':
                value = features.get('price_change_1m', 0.0)
            elif feat_name == 'rsi':
                value = features.get('rsi_14', 50.0)
            elif feat_name == 'volume':
                value = features.get('volume', 1000000.0)
            else:
                value = features.get(feat_name, 0.0)
            feature_array.append(value)
        
        X = np.array([feature_array])
        
        X_scaled = _model_loader.scaler.transform(X)
        
        prediction = _model_loader.model.predict(X_scaled)[0]
        probabilities = _model_loader.model.predict_proba(X_scaled)[0]
        
        model_classes = _model_loader.model.classes_
        
        action_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
        
        if len(model_classes) == 2:
            logger.warning("Модель имеет только 2 класса. Используем правило на основе уверенности для HOLD.")
            pred_idx = np.where(model_classes == prediction)[0]
            if len(pred_idx) > 0:
                pred_confidence = float(probabilities[pred_idx[0]])
            else:
                pred_confidence = 0.5
            
            if pred_confidence < 0.6:
                action = "HOLD"
                confidence = 1.0 - pred_confidence
            else:
                if prediction in action_map:
                    action = action_map[prediction]
                    confidence = pred_confidence
                else:
                    action = "HOLD"
                    confidence = 0.5
        else:
            if prediction not in action_map:
                logger.warning(f"Модель предсказала неизвестный класс: {prediction}. Используем HOLD.")
                action = "HOLD"
                pred_idx = np.where(model_classes == prediction)[0]
                if len(pred_idx) > 0:
                    confidence = float(probabilities[pred_idx[0]])
                else:
                    confidence = 0.5
            else:
                action = action_map[prediction]
                pred_idx = np.where(model_classes == prediction)[0]
                if len(pred_idx) > 0:
                    confidence = float(probabilities[pred_idx[0]])
                else:
                    confidence = 0.5
        
        reason_parts = []
        if features.get('sma_10', 0) > features.get('sma_50', 0):
            reason_parts.append("Price above SMA_50")
        else:
            reason_parts.append("Price below SMA_50")
        
        rsi = features.get('rsi_14', 50)
        if rsi > 70:
            reason_parts.append("RSI overbought")
        elif rsi < 30:
            reason_parts.append("RSI oversold")
        
        price_change = features.get('price_change_1m', 0)
        if price_change > 0:
            reason_parts.append("positive trend")
        else:
            reason_parts.append("negative trend")
        
        reason = ", ".join(reason_parts) if reason_parts else "No clear signal"
        
        result = {
            "action": action,
            "confidence": confidence,
            "reason": reason
        }
        
        logger.info(f"Предсказание: {action} (confidence: {confidence:.2f})")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при предсказании: {e}")
        return {
            "action": "HOLD",
            "confidence": 0.5,
            "reason": f"Prediction error: {str(e)}"
        }

