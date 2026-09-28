from decimal import Decimal
from typing import Any

from app.config.settings import settings


class RuleBasedPricingStrategy:
    def generate(self, product: Any, trigger_reason: str) -> dict[str, Any]:
        demand_ratio = product.demand_velocity / max(product.category_average_demand, 1.0)
        current_price = Decimal(str(product.current_price))
        if trigger_reason == 'demand_spike' or demand_ratio >= settings.demand_spike_multiplier:
            suggested_price = current_price * Decimal('1.12')
            reasoning = 'Demand spike detected; lift price to capture heightened traction.'
        else:
            suggested_price = max(current_price * Decimal('0.96'), Decimal('1.00'))
            reasoning = 'Price modestly trimmed to restore conversion while inventory remains healthy.'

        return {
            'suggested_price': float(round(suggested_price, 2)),
            'reasoning': reasoning,
        }
