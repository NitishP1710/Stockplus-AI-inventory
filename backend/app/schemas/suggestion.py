from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PricingSuggestionRead(BaseModel):
    id: str
    product_id: str
    trigger_reason: str
    suggested_price: Decimal
    rationale: str
    ai_reasoning: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ReorderSuggestionRead(BaseModel):
    id: str
    product_id: str
    trigger_reason: str
    suggested_quantity: int
    rationale: str
    ai_reasoning: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class SuggestionDecisionResult(BaseModel):
    id: str
    status: str
    message: str
