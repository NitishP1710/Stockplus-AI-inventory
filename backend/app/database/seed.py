from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


SEED_PRODUCTS = [
    {
        'id': 'PRD-001',
        'name': 'Alpha Headphones',
        'category': 'electronics',
        'current_price': 149.99,
        'reorder_threshold': 24,
        'stock_level': 18,
        'demand_velocity': 12.5,
        'category_average_demand': 8.4,
        'is_active': True,
    },
    {
        'id': 'PRD-002',
        'name': 'Zen Smartwatch',
        'category': 'electronics',
        'current_price': 229.0,
        'reorder_threshold': 30,
        'stock_level': 41,
        'demand_velocity': 10.8,
        'category_average_demand': 9.2,
        'is_active': True,
    },
    {
        'id': 'PRD-003',
        'name': 'Pulse Water Bottle',
        'category': 'sports',
        'current_price': 32.5,
        'reorder_threshold': 40,
        'stock_level': 12,
        'demand_velocity': 14.9,
        'category_average_demand': 9.1,
        'is_active': True,
    },
    {
        'id': 'PRD-004',
        'name': 'Summit Backpack',
        'category': 'outdoor',
        'current_price': 89.0,
        'reorder_threshold': 21,
        'stock_level': 28,
        'demand_velocity': 9.6,
        'category_average_demand': 8.2,
        'is_active': True,
    },
    {
        'id': 'PRD-005',
        'name': 'Harbor Coffee Beans',
        'category': 'grocery',
        'current_price': 18.5,
        'reorder_threshold': 50,
        'stock_level': 67,
        'demand_velocity': 7.3,
        'category_average_demand': 7.7,
        'is_active': True,
    },
    {
        'id': 'PRD-006',
        'name': 'Luma Desk Lamp',
        'category': 'home',
        'current_price': 64.0,
        'reorder_threshold': 18,
        'stock_level': 26,
        'demand_velocity': 8.4,
        'category_average_demand': 8.0,
        'is_active': True,
    },
    {
        'id': 'PRD-007',
        'name': 'Nimbus Throw Blanket',
        'category': 'home',
        'current_price': 54.0,
        'reorder_threshold': 22,
        'stock_level': 34,
        'demand_velocity': 8.8,
        'category_average_demand': 7.9,
        'is_active': True,
    },
    {
        'id': 'PRD-008',
        'name': 'Velocity Running Shoe',
        'category': 'sports',
        'current_price': 118.0,
        'reorder_threshold': 33,
        'stock_level': 9,
        'demand_velocity': 17.7,
        'category_average_demand': 9.8,
        'is_active': True,
    },
]


async def seed_demo_products(db: AsyncSession) -> None:
    existing = await db.execute(select(Product.id))
    ids = {row[0] for row in existing.fetchall()}
    for payload in SEED_PRODUCTS:
        if payload['id'] not in ids:
            product = Product(**payload)
            db.add(product)
    await db.commit()
