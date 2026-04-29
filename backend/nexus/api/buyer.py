from typing import Optional

from fastapi import APIRouter, HTTPException

from nexus.core.db import get_sqlite_conn

router = APIRouter(prefix="/buyer")


def _table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return bool(cur.fetchone())


def _extract_item_summary(document_text: str) -> str | None:
    if not document_text:
        return None
    try:
        # First bullet under "Items:" block
        # Example: "- 500 × Industrial Thermistor (prod-401)"
        marker = "Items:"
        idx = document_text.find(marker)
        if idx == -1:
            return None
        tail = document_text[idx + len(marker) :]
        lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
        first = next((ln for ln in lines if ln.startswith("- ")), None)
        if not first:
            return None
        return first[2:]
    except Exception:
        return None


def _extract_delivery_by(document_text: str) -> str | None:
    if not document_text:
        return None
    for ln in document_text.splitlines():
        if ln.strip().lower().startswith("delivery by:"):
            return ln.split(":", 1)[1].strip() or None
    return None


@router.get("/{buyer_id}/deals")
async def get_buyer_deals(buyer_id: str, limit: int = 20):
    # Backward-compatible alias for "orders"
    return await get_buyer_orders(buyer_id=buyer_id, limit=limit)


@router.get("/{buyer_id}/orders")
async def get_buyer_orders(buyer_id: str, limit: int = 20):
    conn = get_sqlite_conn()
    cur = conn.cursor()
    try:
        if not _table_exists(cur, "purchase_orders"):
            return []

        # Join supplier name when available
        cur.execute(
            """
            SELECT
              po.id as po_id,
              po.supplier_id as supplier_id,
              COALESCE(s.company_name, po.supplier_id) as supplier_name,
              po.total_amount as total_amount,
              po.currency as currency,
              po.status as status,
              po.created_at as created_at,
              po.document_text as document_text
            FROM purchase_orders po
            LEFT JOIN suppliers s ON s.id = po.supplier_id
            WHERE po.buyer_id = ?
            ORDER BY po.created_at DESC
            LIMIT ?
            """,
            (buyer_id, int(limit)),
        )
        orders = []
        for r in cur.fetchall():
            d = dict(r)
            d["item_summary"] = _extract_item_summary(d.get("document_text"))
            d["delivery_by"] = _extract_delivery_by(d.get("document_text"))
            d.pop("document_text", None)
            orders.append(d)
        return orders
    finally:
        conn.close()


@router.get("/{buyer_id}/orders/{po_id}")
async def get_buyer_order_detail(buyer_id: str, po_id: str):
    conn = get_sqlite_conn()
    cur = conn.cursor()
    try:
        if not _table_exists(cur, "purchase_orders"):
            raise HTTPException(status_code=404, detail="No purchase_orders table")

        cur.execute("SELECT * FROM purchase_orders WHERE id = ? AND buyer_id = ?", (po_id, buyer_id))
        order = cur.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        negotiation = None
        if _table_exists(cur, "po_negotiations") and _table_exists(cur, "negotiation_rounds"):
            cur.execute(
                """
                SELECT session_id
                FROM po_negotiations
                WHERE po_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (po_id,),
            )
            row = cur.fetchone()
            if row and row[0]:
                session_id = row[0]
                cur.execute(
                    """
                    SELECT round_no, speaker, label, message, offer, created_at
                    FROM negotiation_rounds
                    WHERE session_id = ?
                    ORDER BY round_no ASC, id ASC
                    """,
                    (session_id,),
                )
                rounds = [dict(r) for r in cur.fetchall()]
                negotiation = {"session_id": session_id, "rounds": rounds}

        return {"order": dict(order), "negotiation": negotiation}
    finally:
        conn.close()
