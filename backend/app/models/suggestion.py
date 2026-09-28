from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.enums import SuggestionStatus, SuggestionType


class PricingSuggestion(Base):
    __tablename__ = 'pricing_suggestions'

    id = Column(String(64), primary_key=True, index=True)
    product_id = Column(String(64), ForeignKey('products.id'), nullable=False, index=True)
    trigger_reason = Column(String(64), nullable=False, index=True)
    suggested_price = Column(Numeric(10, 2), nullable=False)
    rationale = Column(String(500), nullable=False)
    ai_reasoning = Column(String(500), nullable=True)
    status = Column(String(32), default=SuggestionStatus.PENDING.value, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship('Product', back_populates='pricing_suggestions', lazy='selectin')


class ReorderSuggestion(Base):
    __tablename__ = 'reorder_suggestions'

    id = Column(String(64), primary_key=True, index=True)
    product_id = Column(String(64), ForeignKey('products.id'), nullable=False, index=True)
    trigger_reason = Column(String(64), nullable=False, index=True)
    suggested_quantity = Column(Integer, nullable=False)
    rationale = Column(String(500), nullable=False)
    ai_reasoning = Column(String(500), nullable=True)
    status = Column(String(32), default=SuggestionStatus.PENDING.value, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship('Product', back_populates='reorder_suggestions', lazy='selectin')
