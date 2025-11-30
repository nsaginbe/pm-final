from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Основной метод обработки агента.
        
        Returns:
            Словарь с результатами работы агента
        """
        pass

