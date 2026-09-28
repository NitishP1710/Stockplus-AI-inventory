import asyncio
import logging

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.product import Product
from app.services.suggestion_service import evaluate_product_recommendations

logger = logging.getLogger(__name__)
background_task = None


async def _cycle() -> None:
    async with AsyncSessionLocal() as db:
        products = (await db.execute(select(Product))).scalars().all()
        for product in products:
            try:
                await evaluate_product_recommendations(db, product.id)
            except Exception as exc:
                logger.exception('Background evaluation failed for %s: %s', product.id, exc)


async def recommendation_loop() -> None:
    while True:
        try:
            await _cycle()
        except Exception as exc:
            logger.exception('Recommendation loop failed: %s', exc)
        await asyncio.sleep(3)


async def start_background_loop() -> None:
    global background_task
    if background_task is None or background_task.done():
        background_task = asyncio.create_task(recommendation_loop())
