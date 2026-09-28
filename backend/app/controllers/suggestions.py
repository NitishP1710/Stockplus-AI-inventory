from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.suggestion import PricingSuggestion, ReorderSuggestion
from app.services.suggestion_service import (
    approve_pricing_suggestion,
    approve_reorder_suggestion,
    get_pending_suggestions,
    reject_pricing_suggestion,
    reject_reorder_suggestion,
)

router = APIRouter(prefix='/suggestions', tags=['suggestions'])


@router.get('/pending')
async def pending_suggestions(db: AsyncSession = Depends(get_db)):
    suggestions = await get_pending_suggestions(db)
    return {
        'pricing': [
            {
                'id': item.id,
                'product_id': item.product_id,
                'trigger_reason': item.trigger_reason,
                'suggested_price': str(item.suggested_price),
                'rationale': item.rationale,
                'ai_reasoning': item.ai_reasoning,
                'status': item.status,
                'product_name': item.product.name,
                'category': item.product.category,
            }
            for item in suggestions['pricing']
        ],
        'reorder': [
            {
                'id': item.id,
                'product_id': item.product_id,
                'trigger_reason': item.trigger_reason,
                'suggested_quantity': item.suggested_quantity,
                'rationale': item.rationale,
                'ai_reasoning': item.ai_reasoning,
                'status': item.status,
                'product_name': item.product.name,
                'category': item.product.category,
            }
            for item in suggestions['reorder']
        ],
    }


@router.post('/pricing/{suggestion_id}/accept')
async def accept_pricing(suggestion_id: str, db: AsyncSession = Depends(get_db)):
    return await approve_pricing_suggestion(db, suggestion_id)


@router.post('/pricing/{suggestion_id}/reject')
async def reject_pricing(suggestion_id: str, db: AsyncSession = Depends(get_db)):
    return await reject_pricing_suggestion(db, suggestion_id)


@router.post('/reorder/{suggestion_id}/accept')
async def accept_reorder(suggestion_id: str, db: AsyncSession = Depends(get_db)):
    return await approve_reorder_suggestion(db, suggestion_id)


@router.post('/reorder/{suggestion_id}/reject')
async def reject_reorder(suggestion_id: str, db: AsyncSession = Depends(get_db)):
    return await reject_reorder_suggestion(db, suggestion_id)
