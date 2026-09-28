from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.product import Product
from app.schemas.product import ProductRead, ProductSummary
from app.services.suggestion_service import evaluate_product_recommendations

router = APIRouter(prefix='/products', tags=['products'])


@router.get('', response_model=list[ProductRead])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[Product]:
    result = await db.execute(select(Product).order_by(Product.name.asc()))
    return result.scalars().all()


@router.get('/summary')
async def product_summary(db: AsyncSession = Depends(get_db)) -> ProductSummary:
    products = (await db.execute(select(Product))).scalars().all()
    pending = 0
    low_stock = 0
    demand_spike = 0
    for product in products:
        if product.stock_level < product.reorder_threshold:
            low_stock += 1
        demand_ratio = product.demand_velocity / max(product.category_average_demand, 1.0)
        if demand_ratio >= 1.5:
            demand_spike += 1
    return {
        'total_products': len(products),
        'low_stock_count': low_stock,
        'demand_spike_count': demand_spike,
        'pending_suggestions': pending,
    }


@router.get('/{product_id}', response_model=ProductRead)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='Product not found')
    return product


@router.post('/{product_id}/evaluate')
async def evaluate_product(product_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    created = await evaluate_product_recommendations(db, product_id)
    return {'product_id': product_id, 'generated': len(created), 'suggestions': created}
