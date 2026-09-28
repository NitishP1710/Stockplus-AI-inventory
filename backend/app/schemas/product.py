from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    id: str
    name: str
    category: str
    current_price: Decimal
    reorder_threshold: int
    stock_level: int
    demand_velocity: float
    category_average_demand: float
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ProductRead(ProductBase):
    pass


class ProductSummary(BaseModel):
    total_products: int
    low_stock_count: int
    demand_spike_count: int
    pending_suggestions: int
