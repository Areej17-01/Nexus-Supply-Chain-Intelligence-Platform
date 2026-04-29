from typing import Optional
from fastapi import APIRouter, HTTPException
from nexus.api.models import SupplierCatalogItem, SupplierRegistrationRequest
from nexus.core.db import get_sqlite_conn
from supplier.supplier_registry import SupplierRegistry

router = APIRouter(prefix="/supplier")

@router.get("/{supplier_id}/orders")
async def get_supplier_orders(supplier_id: str, status: Optional[str] = None):
    conn = get_sqlite_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_line_items'")
        if not cur.fetchone():
            return []
        if status:
            cur.execute("SELECT * FROM order_line_items WHERE supplier_id = ? AND status = ?", (supplier_id, status))
        else:
            cur.execute("SELECT * FROM order_line_items WHERE supplier_id = ?", (supplier_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.get("/{supplier_id}/catalog")
async def get_supplier_catalog(supplier_id: str):
    conn = get_sqlite_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM supplier_products WHERE supplier_id = ?", (supplier_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.post("/{supplier_id}/catalog")
async def update_catalog(supplier_id: str, item: SupplierCatalogItem):
    # Upsert via registry helper (works for both SQLite/Postgres backends)
    product_id = f"{supplier_id}-{item.product_name.lower().strip().replace(' ', '-')}"
    try:
        result = SupplierRegistry.add_product_to_supplier(
            supplier_id=supplier_id,
            product_id=product_id,
            product_name=item.product_name,
            category=item.product_category,
            unit_price=float(item.base_unit_price),
            stock_quantity=int(item.stock_available),
            lead_time_days=int(item.lead_time_days),
            certifications_required=[],
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
async def register_supplier(req: SupplierRegistrationRequest):
    try:
        result = SupplierRegistry.register_supplier(
            supplier_id=req.supplier_id,
            company_name=req.company_name,
            country=req.country,
            region=req.region,
            certifications=req.certifications,
            capabilities=[],
            contact_email=req.contact_email,
            trust_score=req.trust_score,
            negotiation_style=req.negotiation_style
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
