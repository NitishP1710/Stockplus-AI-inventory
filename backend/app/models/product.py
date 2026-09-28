from sqlalchemy import Boolean, Column, Float, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(128), nullable=False, index=True)
    current_price = Column(Numeric(10, 2), nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=0)
    stock_level = Column(Integer, nullable=False, default=0)
    demand_velocity = Column(Float, nullable=False, default=0.0)
    category_average_demand = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)

    pricing_suggestions = relationship('PricingSuggestion', back_populates='product', cascade='all, delete-orphan')
    reorder_suggestions = relationship('ReorderSuggestion', back_populates='product', cascade='all, delete-orphan')
