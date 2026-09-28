from datetime import datetime, timezone
from decimal import Decimal
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.config.settings import settings
from app.models.enums import SuggestionStatus
from app.models.product import Product
from app.models.suggestion import PricingSuggestion, ReorderSuggestion
from app.strategies.pricing import RuleBasedPricingStrategy
from app.strategies.reorder import RuleBasedReorderStrategy

pricing_strategy = RuleBasedPricingStrategy()
reorder_strategy = RuleBasedReorderStrategy()
ai_gateway = AIGateway()


def _now():
    return datetime.now(timezone.utc)


async def _product_by_id(db: AsyncSession, product_id: str) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return product


async def _pending_duplicate_exists(db: AsyncSession, product_id: str, trigger_reason: str, kind: str) -> bool:
    table = PricingSuggestion if kind == 'pricing' else ReorderSuggestion
    query = select(table.id).where(
        table.product_id == product_id,
        table.trigger_reason == trigger_reason,
        table.status == SuggestionStatus.PENDING.value,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def evaluate_product_recommendations(db: AsyncSession, product_id: str) -> list[dict]:
    product = await _product_by_id(db, product_id)
    recommendations: list[dict] = []

    inventory_low = product.stock_level < product.reorder_threshold
    demand_ratio = product.demand_velocity / max(product.category_average_demand, 1.0)
    demand_spike = demand_ratio >= settings.demand_spike_multiplier

    if inventory_low:
        trigger_reason = 'inventory_low'
        if not await _pending_duplicate_exists(db, product_id, trigger_reason, 'reorder'):
            suggested = reorder_strategy.generate(product, trigger_reason)
            ai_payload = await ai_gateway.get_recommendation(product, trigger_reason, suggested)
            suggestion = ReorderSuggestion(
                id=f"RO-{uuid.uuid4().hex[:8]}",
                product_id=product_id,
                trigger_reason=trigger_reason,
                suggested_quantity=int(ai_payload.get('suggested_quantity', suggested['suggested_quantity'])),
                rationale=suggested['reasoning'],
                ai_reasoning=ai_payload.get('reasoning', suggested['reasoning']),
                status=SuggestionStatus.PENDING.value,
            )
            db.add(suggestion)
            recommendations.append({'type': 'reorder', 'id': suggestion.id, 'trigger_reason': trigger_reason})

    if demand_spike:
        trigger_reason = 'demand_spike'
        if not await _pending_duplicate_exists(db, product_id, trigger_reason, 'pricing'):
            suggested = pricing_strategy.generate(product, trigger_reason)
            ai_payload = await ai_gateway.get_recommendation(product, trigger_reason, suggested)
            suggestion = PricingSuggestion(
                id=f"PR-{uuid.uuid4().hex[:8]}",
                product_id=product_id,
                trigger_reason=trigger_reason,
                suggested_price=Decimal(str(ai_payload.get('suggested_price', suggested['suggested_price']))),
                rationale=suggested['reasoning'],
                ai_reasoning=ai_payload.get('reasoning', suggested['reasoning']),
                status=SuggestionStatus.PENDING.value,
            )
            db.add(suggestion)
            recommendations.append({'type': 'pricing', 'id': suggestion.id, 'trigger_reason': trigger_reason})

    await db.commit()
    return recommendations


async def get_pending_suggestions(db: AsyncSession):
    pricing = await db.execute(
        select(PricingSuggestion)
        .options(selectinload(PricingSuggestion.product))
        .where(PricingSuggestion.status == SuggestionStatus.PENDING.value)
        .order_by(PricingSuggestion.created_at.desc())
    )
    reorder = await db.execute(
        select(ReorderSuggestion)
        .options(selectinload(ReorderSuggestion.product))
        .where(ReorderSuggestion.status == SuggestionStatus.PENDING.value)
        .order_by(ReorderSuggestion.created_at.desc())
    )
    return {'pricing': pricing.scalars().all(), 'reorder': reorder.scalars().all()}


async def approve_pricing_suggestion(db: AsyncSession, suggestion_id: str):
    suggestion = await db.get(PricingSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail='Pricing suggestion not found')
    if suggestion.status != SuggestionStatus.PENDING.value:
        raise HTTPException(status_code=409, detail='Invalid state transition: suggestion is not pending')

    suggestion.status = SuggestionStatus.ACCEPTED.value
    suggestion.accepted_at = _now()
    product = await _product_by_id(db, suggestion.product_id)
    product.current_price = suggestion.suggested_price
    await db.commit()
    return {'id': suggestion.id, 'status': suggestion.status, 'message': 'Pricing update applied to product'}


async def reject_pricing_suggestion(db: AsyncSession, suggestion_id: str):
    suggestion = await db.get(PricingSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail='Pricing suggestion not found')
    if suggestion.status != SuggestionStatus.PENDING.value:
        raise HTTPException(status_code=409, detail='Invalid state transition: suggestion is not pending')
    suggestion.status = SuggestionStatus.REJECTED.value
    suggestion.rejected_at = _now()
    await db.commit()
    return {'id': suggestion.id, 'status': suggestion.status, 'message': 'Pricing suggestion rejected'}


async def approve_reorder_suggestion(db: AsyncSession, suggestion_id: str):
    suggestion = await db.get(ReorderSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail='Reorder suggestion not found')
    if suggestion.status != SuggestionStatus.PENDING.value:
        raise HTTPException(status_code=409, detail='Invalid state transition: suggestion is not pending')

    suggestion.status = SuggestionStatus.ACCEPTED.value
    suggestion.accepted_at = _now()
    product = await _product_by_id(db, suggestion.product_id)
    product.stock_level = product.stock_level + suggestion.suggested_quantity
    await db.commit()
    return {'id': suggestion.id, 'status': suggestion.status, 'message': 'Reorder applied to inventory'}


async def reject_reorder_suggestion(db: AsyncSession, suggestion_id: str):
    suggestion = await db.get(ReorderSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail='Reorder suggestion not found')
    if suggestion.status != SuggestionStatus.PENDING.value:
        raise HTTPException(status_code=409, detail='Invalid state transition: suggestion is not pending')
    suggestion.status = SuggestionStatus.REJECTED.value
    suggestion.rejected_at = _now()
    await db.commit()
    return {'id': suggestion.id, 'status': suggestion.status, 'message': 'Reorder suggestion rejected'}
