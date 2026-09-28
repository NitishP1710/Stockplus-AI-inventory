from abc import ABC, abstractmethod
from typing import Any


class PricingStrategy(ABC):
    @abstractmethod
    def generate(self, product: Any, trigger_reason: str) -> dict[str, Any]:
        raise NotImplementedError


class ReorderStrategy(ABC):
    @abstractmethod
    def generate(self, product: Any, trigger_reason: str) -> dict[str, Any]:
        raise NotImplementedError
