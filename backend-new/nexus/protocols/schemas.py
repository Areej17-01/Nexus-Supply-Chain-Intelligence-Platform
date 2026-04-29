from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class ProcurementRequest(BaseModel):
    request: str
    destination_region: Optional[str] = None
    budget: Optional[float] = None
    deadline_days: Optional[int] = 7


class BOMItem(BaseModel):
    part_name: str
    category: str
    quantity: int
    unit: str = "units"


class BOM(BaseModel):
    product: str
    items: List[BOMItem]
    destination_region: str
    deadline_days: int
    budget: Optional[float]


class RFQMessage(BaseModel):
    type: Literal["rfq"]
    negotiation_id: str
    buyer_id: str
    supplier_id: str
    items: List[BOMItem]
    destination_region: str
    deadline_days: int
    required_certifications: List[str] = []


class QuoteResponse(BaseModel):
    type: Literal["quote"]
    negotiation_id: str
    supplier_id: str
    supplier_name: str
    unit_price: float
    total_price: float
    lead_time_days: int
    currency: str = "EUR"
    certifications: List[str]
    valid_until: str
    rationale: str = ""


class CounterOfferMessage(BaseModel):
    type: Literal["counter_offer"]
    negotiation_id: str
    buyer_price: float
    round: int
    message: str


class NegotiationResponse(BaseModel):
    type: Literal["negotiation_response"]
    negotiation_id: str
    supplier_id: str
    accepted: bool
    counter_price: Optional[float]
    rationale: str
    final: bool


class RetryRequest(BaseModel):
    negotiation_id: str
    supplier_id: str
    updated_budget: Optional[float] = None
    updated_deadline_days: Optional[int] = None


class ProcurementResult(BaseModel):
    success: bool
    negotiation_id: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    final_price: Optional[float] = None
    total_cost: Optional[float] = None
    lead_time_days: Optional[int] = None
    rounds_taken: int = 0
    failure_reason: Optional[str] = None
    closest_offer: Optional[dict] = None
    other_options: Optional[List[dict]] = None
    suggestion: Optional[str] = None
    all_initial_quotes: List[QuoteResponse] = []
    contract_id: Optional[str] = None


class TranscriptResponse(BaseModel):
    negotiation_id: str
    supplier: str
    product: str
    status: str
    duration_seconds: int
    transcript: list
    summary: dict


class SupplierUpsert(BaseModel):
    supplier_id: str
    company_name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    capabilities: List[str] = []
    certifications: List[str] = []
    trust_score: Optional[float] = None
    lead_time_days: Optional[int] = None
