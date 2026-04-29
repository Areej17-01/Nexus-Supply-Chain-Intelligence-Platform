from datetime import datetime, timedelta
from uuid import uuid4

from nexus.core.logger import setup_logger

log = setup_logger("nexus.execution.contract")


class ContractGenerator:
    def generate_po(self, buyer_id: str, supplier: dict, agreement: dict, logistics: dict) -> dict:
        po_id = f"PO-{uuid4().hex[:8].upper()}"
        delivery_by = (datetime.utcnow() + timedelta(days=int(logistics.get("estimated_days", 14)))).strftime("%Y-%m-%d")
        po_text = f"""PURCHASE ORDER {po_id}

Buyer: {buyer_id}
Supplier: {supplier.get('name') or supplier.get('company_name')}
Supplier ID: {supplier.get('id') or supplier.get('supplier_id')}

Items:
{self._format_items(agreement.get('line_items', []))}

Agreed Total: {agreement.get('final_price')} {agreement.get('currency', 'EUR')}
Payment Terms: {agreement.get('payment_terms', 'Net-30')}
Delivery Route: {logistics.get('route')}
Delivery By: {delivery_by}
Carrier: {logistics.get('carrier')}

Quality Acceptance:
- Supplier must provide products matching quoted specifications.
- Buyer may reject non-conforming goods within 7 business days.

Late Delivery Penalty:
- 2% of order value per delayed week after agreed delivery date.

Status: Supplier digitally confirmed through NEXUS A2A protocol.
"""
        result = {
            "po_id": po_id,
            "status": "generated",
            "supplier_id": supplier.get("id") or supplier.get("supplier_id"),
            "supplier_name": supplier.get("name") or supplier.get("company_name"),
            "buyer_id": buyer_id,
            "total": agreement.get("final_price"),
            "currency": agreement.get("currency", "EUR"),
            "delivery_by": delivery_by,
            "document_text": po_text,
            "download_name": f"{po_id}.txt",
        }
        log.info("[CONTRACT] generated po_id=%s supplier_id=%s total=%s", po_id, result["supplier_id"], result["total"])
        return result

    def _format_items(self, line_items: list) -> str:
        if not line_items:
            return "- Items from accepted quote"
        return "\n".join(
            f"- {item.get('quantity')} × {item.get('product_name')} ({item.get('product_id')})"
            for item in line_items
        )
