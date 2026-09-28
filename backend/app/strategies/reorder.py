from typing import Any


class RuleBasedReorderStrategy:
    def generate(self, product: Any, trigger_reason: str) -> dict[str, Any]:
        shortage = max(product.reorder_threshold - product.stock_level, 0)
        suggested_quantity = max(shortage + 12, product.reorder_threshold)
        reasoning = 'Inventory is below threshold; replenish to avoid stock-out risk.'
        if trigger_reason == 'inventory_low':
            reasoning = 'Inventory dropped below reorder threshold; trigger a replenishment quantity.'

        return {
            'suggested_quantity': int(suggested_quantity),
            'reasoning': reasoning,
        }
