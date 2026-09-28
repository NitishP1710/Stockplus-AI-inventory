import json
from typing import Any

import httpx

from app.config.settings import settings


class AIGateway:
    async def get_recommendation(self, product: Any, trigger_reason: str, rule_based: dict[str, Any]) -> dict[str, Any]:
        if settings.llm_provider.lower() == 'mock':
            return {
                'suggested_price': float(rule_based.get('suggested_price', product.current_price)),
                'suggested_quantity': int(rule_based.get('suggested_quantity', product.reorder_threshold)),
                'reasoning': 'Mock LLM: deterministic fallback recommended for local development.',
            }

        payload = {
            'model': settings.llm_model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'Return JSON only with keys: suggested_price, suggested_quantity, reasoning. Use sensible retail and reorder guidance.',
                },
                {
                    'role': 'user',
                    'content': (
                        f"Product: {product.name} | category: {product.category} | stock: {product.stock_level} | "
                        f"threshold: {product.reorder_threshold} | demand velocity: {product.demand_velocity} | "
                        f"category avg: {product.category_average_demand} | trigger: {trigger_reason}"
                    ),
                },
            ],
            'temperature': 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    json=payload,
                    headers={'Authorization': f'Bearer {settings.llm_api_key}', 'Content-Type': 'application/json'},
                )
                response.raise_for_status()
                data = response.json()
                content = data['choices'][0]['message']['content']
                return json.loads(content)
        except Exception:
            return {
                'suggested_price': float(rule_based.get('suggested_price', product.current_price)),
                'suggested_quantity': int(rule_based.get('suggested_quantity', product.reorder_threshold)),
                'reasoning': 'LLM unavailable; fallback to deterministic rule-based output.',
            }
