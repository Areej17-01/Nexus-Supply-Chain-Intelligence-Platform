from typing import List, Optional
from pydantic import BaseModel

class RFQItem(BaseModel):
    product_id: str
    quantity: int

class RFQRequest(BaseModel):
    buyer_id: str
    items: List[RFQItem]
    delivery_region: str
    deadline_days: int
    max_budget: Optional[float] = None
    required_certifications: List[str] = []
    negotiation_style: Optional[str] = "balanced"

class SupplierRegistrationRequest(BaseModel):
    supplier_id: str
    company_name: str
    country: str
    region: str
    certifications: List[str]
    contact_email: str
    trust_score: Optional[float] = 0.5
    negotiation_style: Optional[str] = "balanced"

class SupplierDiscoveryRequest(BaseModel):
    capability: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    min_trust_score: Optional[float] = 0.5
    certifications_required: List[str] = []

class SupplierCatalogItem(BaseModel):
    product_name: str
    product_category: str
    base_unit_price: float
    stock_available: int
    lead_time_days: int
    specs: dict = {}
