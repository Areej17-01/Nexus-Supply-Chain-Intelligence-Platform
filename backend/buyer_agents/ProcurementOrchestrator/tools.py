import asyncio
import json
import re
import uuid
from datetime import date, datetime, timedelta

import httpx

from nexus.core.config import PORT
from nexus.core.db import get_db_conn as get_conn
from nexus.core.logger import setup_logger

log = setup_logger("procurement_orchestrator.tools")


def _is_sqlite_conn(conn) -> bool:
    return conn.__class__.__module__.startswith("sqlite3")


def _ph(conn) -> str:
    return "?" if _is_sqlite_conn(conn) else "%s"


def _safe_parse_iso_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except Exception:
            return datetime.utcnow().date()
    return datetime.utcnow().date()


def _ensure_core_tables(cur):
    # Minimal schema required for the ADK buyer orchestrator tools.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS buyers (
            id TEXT PRIMARY KEY,
            company_name TEXT,
            country TEXT,
            region TEXT,
            industry TEXT,
            negotiation_style TEXT,
            is_active INTEGER DEFAULT 1,
            registered_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            buyer_id TEXT,
            status TEXT,
            priority TEXT,
            delivery_region TEXT,
            delivery_deadline TEXT,
            total_budget_ceiling REAL,
            negotiation_style TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_line_items (
            id TEXT PRIMARY KEY,
            order_id TEXT,
            supplier_id TEXT,
            product_id TEXT,
            product_name TEXT,
            product_category TEXT,
            quantity INTEGER,
            target_unit_price REAL,
            max_unit_price REAL,
            required_certifications TEXT,
            agent_instruction TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    # Used by the UI order detail view.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS po_negotiations (
            po_id TEXT,
            session_id TEXT,
            supplier_id TEXT,
            created_at TEXT
        )
        """
    )


def _ensure_buyer_exists(conn, cur, buyer_id: str) -> str:
    _ensure_core_tables(cur)
    if not buyer_id or not str(buyer_id).strip():
        buyer_id = "buyer-unknown"

    placeholder = _ph(conn)
    cur.execute(f"SELECT id FROM buyers WHERE id = {placeholder}", (buyer_id,))
    row = cur.fetchone()
    if row:
        return buyer_id

    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        f"""
        INSERT INTO buyers (id, company_name, country, region, industry, negotiation_style, is_active, registered_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            buyer_id,
            f"AutoCreated {buyer_id}",
            "Unknown",
            "Unknown",
            None,
            "balanced",
            1,
            now,
        ),
    )
    return buyer_id


def _extract_json_block(text: str) -> dict | None:
    if not text or not isinstance(text, str):
        return None
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        return json.loads(match.group(0))
    except Exception:
        return None


def _event_text_from_run(events: list) -> str:
    if not isinstance(events, list):
        return ""
    for ev in reversed(events):
        if not isinstance(ev, dict):
            continue
        content = ev.get("content") or {}
        parts = content.get("parts") or []
        texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
        if texts:
            return "\n".join(texts)
    return ""


def parse_intent_and_create_order(
    buyer_id: str,
    product: str,
    quantity: int,
    target_price: float,
    max_price: float,
    delivery_region: str,
    deadline_days: int,
    instruction: str = "",
    priority: str = "standard",
    negotiation_style: str = "balanced",
    required_certifications: list | None = None,
) -> dict:
    """Persist buyer intent into `orders` + `order_line_items` using the CURRENT DB schema.

    This does NOT depend on the legacy `supplier_catalog` table.
    It uses `supplier_products` as the canonical catalog.
    """

    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    try:
        buyer_id = _ensure_buyer_exists(conn, cur, buyer_id)

        if not product:
            return {"success": False, "error": "Missing product"}

        quantity = int(quantity or 1)
        target_price = float(target_price or 0)
        max_price = float(max_price or target_price or 0)
        deadline_days = int(deadline_days or 14)
        delivery_region = delivery_region or "ANY"

        order_id = f"ord-{uuid.uuid4().hex[:8]}"
        line_item_id = f"li-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        deadline_date = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

        _ensure_core_tables(cur)

        cur.execute(
            f"""
            INSERT INTO orders
            (id, buyer_id, status, priority, delivery_region, delivery_deadline, total_budget_ceiling, negotiation_style, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                order_id,
                buyer_id,
                "negotiating",
                priority,
                delivery_region,
                deadline_date,
                float(max_price) * float(quantity),
                negotiation_style,
                now,
            ),
        )

        # Resolve a baseline product_id/category from `supplier_products` when possible.
        cur.execute(
            f"""
            SELECT product_id, product_name, category, unit_price, stock_quantity, lead_time_days
            FROM supplier_products
            WHERE (
                LOWER(product_name) LIKE LOWER({placeholder})
                OR LOWER(category) LIKE LOWER({placeholder})
            )
            ORDER BY unit_price ASC, stock_quantity DESC
            LIMIT 1
            """,
            (f"%{product}%", f"%{product}%"),
        )
        best = cur.fetchone()
        resolved_product_id = (best["product_id"] if best else None)
        resolved_category = (best["category"] if best else "unknown")

        cur.execute(
            f"""
            INSERT INTO order_line_items
            (id, order_id, supplier_id, product_id, product_name, product_category, quantity,
             target_unit_price, max_unit_price, required_certifications, agent_instruction, status, created_at)
            VALUES ({placeholder}, {placeholder}, NULL, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                line_item_id,
                order_id,
                resolved_product_id,
                product,
                resolved_category,
                quantity,
                target_price,
                max_price,
                json.dumps(required_certifications or []),
                instruction,
                "discovering",
                now,
            ),
        )

        conn.commit()
        return {
            "success": True,
            "order_id": order_id,
            "line_item_id": line_item_id,
            "resolved_product_id": resolved_product_id,
            "product_category": resolved_category,
            "confidence_score": 0.8 if best else 0.55,
        }
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        log.exception("parse_intent_and_create_order failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def discover_suppliers_for_line_item(line_item_id: str, top_k: int = 5) -> dict:
    """Rank suppliers from `suppliers` + `supplier_products` + `trust_scores`."""

    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        _ensure_core_tables(cur)

        cur.execute(
            f"""
            SELECT oli.id, oli.order_id, oli.product_category, oli.quantity, oli.target_unit_price,
                   oli.required_certifications,
                   o.buyer_id, o.delivery_region, o.delivery_deadline
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = {placeholder}
            """,
            (line_item_id,),
        )
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        category = li["product_category"]
        quantity = int(li["quantity"] or 1)
        target_unit_price = float(li["target_unit_price"] or 0)
        delivery_deadline = li["delivery_deadline"]
        deadline = _safe_parse_iso_date(delivery_deadline) if delivery_deadline else datetime.utcnow().date()

        cur.execute(
            f"""
            SELECT
              s.id AS supplier_id,
              s.company_name AS supplier_name,
              s.region,
              s.certifications,
              sp.product_id,
              sp.product_name,
              sp.unit_price,
              sp.stock_quantity,
              sp.lead_time_days,
              COALESCE(ts.overall_score, s.trust_score, 0.5) AS trust_score
            FROM suppliers s
            JOIN supplier_products sp ON sp.supplier_id = s.id
            LEFT JOIN trust_scores ts ON ts.entity_id = s.id AND ts.entity_type = 'supplier'
            WHERE s.is_active = 1
              AND LOWER(sp.category) = LOWER({placeholder})
              AND sp.stock_quantity >= {placeholder}
            """,
            (category, quantity),
        )
        rows = cur.fetchall() or []
        if not rows:
            return {
                "success": True,
                "line_item_id": line_item_id,
                "shortlist": [],
                "message": "No suppliers match current demand and category.",
            }

        ranked = []
        for r in rows:
            days_left = max((deadline - datetime.utcnow().date()).days, 1)
            lead_time = int(r["lead_time_days"] or 14)
            lead_fit = 1.0 if lead_time <= days_left else 0.3
            unit_price = float(r["unit_price"] or 0.0)
            price_fit = 1.0 if (target_unit_price and unit_price <= target_unit_price) else 0.6
            trust = float(r["trust_score"] or 0.5)
            score = round((0.35 * lead_fit) + (0.35 * trust) + (0.30 * price_fit), 3)

            ranked.append(
                {
                    "supplier_id": r["supplier_id"],
                    "supplier_name": r["supplier_name"],
                    "region": r["region"],
                    "certifications": r["certifications"],
                    "product_id": r["product_id"],
                    "quoted_product": r["product_name"],
                    "base_unit_price": unit_price,
                    "lead_time_days": lead_time,
                    "stock_quantity": int(r["stock_quantity"] or 0),
                    "trust_score": trust,
                    "fit_score": score,
                    "rationale": f"lead_fit={lead_fit}, price_fit={price_fit}, trust={trust:.2f}",
                }
            )

        shortlist = sorted(ranked, key=lambda x: x["fit_score"], reverse=True)[: int(top_k or 5)]
        return {"success": True, "line_item_id": line_item_id, "shortlist": shortlist}

    except Exception as e:
        log.exception("discover_suppliers_for_line_item failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def select_supplier_for_line_item(line_item_id: str, supplier_id: str) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    try:
        _ensure_core_tables(cur)

        cur.execute(f"SELECT id, order_id FROM order_line_items WHERE id = {placeholder}", (line_item_id,))
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        cur.execute(f"SELECT id FROM suppliers WHERE id = {placeholder} AND is_active = 1", (supplier_id,))
        s = cur.fetchone()
        if not s:
            return {"success": False, "error": f"supplier_id not found or inactive: {supplier_id}"}

        cur.execute(
            f"""
            UPDATE order_line_items
            SET supplier_id = {placeholder},
                status = {placeholder}
            WHERE id = {placeholder}
            """,
            (supplier_id, "rfq_ready", line_item_id),
        )
        conn.commit()
        return {"success": True, "line_item_id": line_item_id, "order_id": li["order_id"], "supplier_id": supplier_id}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        log.exception("select_supplier_for_line_item failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_macro_context(product_category: str, delivery_region: str) -> dict:
    # Current demo DB doesn't ship macro_signals; return safe default.
    return {"success": True, "urgency": "normal", "signals": [], "note": "macro_signals not configured"}


def assess_supplier_risk(supplier_id: str, buyer_id: str | None = None) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    try:
        cur.execute(
            f"""
            SELECT s.id, COALESCE(ts.overall_score, s.trust_score, 0.5) AS trust,
                   COALESCE(ts.delivery_score, 0.5) AS delivery,
                   COALESCE(ts.quality_score, 0.5) AS quality,
                   COALESCE(ts.supplier_dispute_rate, 0.0) AS disputes
            FROM suppliers s
            LEFT JOIN trust_scores ts ON ts.entity_id = s.id AND ts.entity_type = 'supplier'
            WHERE s.id = {placeholder}
            """,
            (supplier_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"success": False, "error": f"supplier_id not found: {supplier_id}"}

        trust = float(row["trust"] or 0.5)
        delivery = float(row["delivery"] or 0.5)
        quality = float(row["quality"] or 0.5)
        disputes = float(row["disputes"] or 0.0)
        risk_score = round((0.40 * (1 - trust)) + (0.25 * (1 - delivery)) + (0.20 * (1 - quality)) + (0.15 * disputes), 3)

        if risk_score >= 0.60:
            level = "high"
        elif risk_score >= 0.35:
            level = "medium"
        else:
            level = "low"

        blockers = ["require_hitl_before_commit"] if level == "high" else []
        return {
            "success": True,
            "supplier_id": supplier_id,
            "buyer_id": buyer_id,
            "risk_level": level,
            "risk_score": risk_score,
            "blockers": blockers,
            "dimensions": {"trust": trust, "delivery": delivery, "quality": quality, "disputes": disputes},
        }
    except Exception as e:
        log.exception("assess_supplier_risk failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def create_negotiation_strategy(
    line_item_id: str,
    supplier_id: str,
    macro_urgency: str = "normal",
    risk_level: str = "medium",
) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        cur.execute(
            f"""
            SELECT oli.target_unit_price, oli.max_unit_price, oli.quantity, o.buyer_id, oli.product_category
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = {placeholder}
            """,
            (line_item_id,),
        )
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        cur.execute(
            f"""
            SELECT unit_price, lead_time_days
            FROM supplier_products
            WHERE supplier_id = {placeholder}
              AND LOWER(category) = LOWER({placeholder})
            ORDER BY unit_price ASC
            LIMIT 1
            """,
            (supplier_id, li["product_category"]),
        )
        market_row = cur.fetchone()
        market = float(market_row["unit_price"] if market_row else 0.0)

        target = float(li["target_unit_price"] or 0.0)
        max_price = float(li["max_unit_price"] or target or 0.0)

        open_offer = round(min(target, market * 0.95) if market else target, 2)
        counter_offer = round(min(max(target, market * 0.98) if market else target, max_price), 2)
        walkaway = round(max_price, 2)

        if macro_urgency == "close_fast":
            counter_offer = round(min(max_price, max(counter_offer, market)), 2) if market else counter_offer

        hitl_required = (risk_level == "high")
        return {
            "success": True,
            "line_item_id": line_item_id,
            "supplier_id": supplier_id,
            "strategy": {
                "open_offer": open_offer,
                "counter_offer": counter_offer,
                "walkaway_price_internal_only": walkaway,
                "hitl_required": hitl_required,
                "hitl_reason": "high_risk" if hitl_required else None,
            },
            "safety_note": "Never disclose walkaway_price_internal_only to supplier.",
        }
    except Exception as e:
        log.exception("create_negotiation_strategy failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


async def _call_supplier_adk(run_payload: dict) -> list | dict:
    url = f"http://127.0.0.1:{int(PORT)}/supplier/run"
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(4):
            resp = await client.post(url, json=run_payload)
            if resp.status_code != 429:
                resp.raise_for_status()
                return resp.json()
            wait = (2 ** attempt) * 10
            log.warning("Supplier ADK 429 – retrying in %ss (attempt %s/4)", wait, attempt + 1)
            await asyncio.sleep(wait)
        resp.raise_for_status()
        return resp.json()


def send_message_to_supplier(
    supplier_id: str,
    buyer_id: str,
    session_id: str,
    message: dict,
) -> dict:
    """Send a JSON message to the ADK supplier `QuoteAgent` (multi-turn negotiation supported).

    `message` is serialized and provided as the user's message content.
    """

    payload = {
        "appName": "QuoteAgent",
        "userId": buyer_id or "buyer-nexus",
        "sessionId": session_id,
        "newMessage": {"role": "user", "parts": [{"text": json.dumps({**message, "supplier_id": supplier_id, "buyer_id": buyer_id})}]},
    }

    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        events = loop.run_until_complete(_call_supplier_adk(payload))
        text = _event_text_from_run(events if isinstance(events, list) else [])
        parsed = _extract_json_block(text) or ({"raw": text} if text else {})
        return {
            "success": True,
            "supplier_id": supplier_id,
            "session_id": session_id,
            "events": events,
            "text": text,
            "parsed": parsed,
        }
    except Exception as e:
        log.exception("send_message_to_supplier failed")
        return {"success": False, "supplier_id": supplier_id, "session_id": session_id, "error": str(e)}


def send_rfq_to_supplier(supplier_id: str, line_item_id: str) -> dict:
    """Convenience tool: build RFQ from the stored line item and call supplier agent."""

    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        _ensure_core_tables(cur)

        cur.execute(
            f"""
            SELECT oli.id, oli.order_id, oli.product_id, oli.product_name, oli.product_category, oli.quantity,
                   oli.required_certifications, o.buyer_id, o.delivery_region, o.delivery_deadline
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = {placeholder}
            """,
            (line_item_id,),
        )
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        buyer_id = li["buyer_id"]
        delivery_region = li["delivery_region"] or "ANY"
        delivery_deadline = li["delivery_deadline"]
        deadline = _safe_parse_iso_date(delivery_deadline) if delivery_deadline else datetime.utcnow().date()
        deadline_days = max((deadline - datetime.utcnow().date()).days, 1)

        try:
            required_certs = json.loads(li["required_certifications"] or "[]")
        except Exception:
            required_certs = []

        rfq = {
            "action": "RFQ",
            "delivery_region": delivery_region,
            "deadline_days": int(deadline_days),
            "required_certifications": required_certs,
            "items": [
                {
                    "product_id": li["product_id"],
                    "category": li["product_category"],
                    "quantity": int(li["quantity"] or 1),
                }
            ],
        }

        session_id = f"neg-{uuid.uuid4().hex[:8]}"
        return send_message_to_supplier(
            supplier_id=supplier_id,
            buyer_id=buyer_id,
            session_id=session_id,
            message=rfq,
        )
    except Exception as e:
        log.exception("send_rfq_to_supplier failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def persist_negotiation_round(
    session_id: str,
    round_no: int,
    speaker: str,
    label: str,
    message: str,
    offer: float | None = None,
) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        # Tables exist in seed, but ensure for safety.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS negotiation_sessions (
                id TEXT PRIMARY KEY,
                supplier_id TEXT,
                buyer_id TEXT,
                status TEXT,
                initial_price REAL,
                final_price REAL,
                savings_pct REAL,
                reward REAL,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS negotiation_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                round_no INTEGER,
                speaker TEXT,
                label TEXT,
                message TEXT,
                offer REAL,
                created_at TEXT
            )
            """
        )

        now = datetime.utcnow().isoformat() + "Z"
        cur.execute(
            f"""
            INSERT INTO negotiation_rounds (session_id, round_no, speaker, label, message, offer, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (session_id, int(round_no), speaker, label, message, offer, now),
        )
        conn.commit()
        return {"success": True, "session_id": session_id, "round_no": int(round_no)}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        log.exception("persist_negotiation_round failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def create_purchase_order(
    supplier_id: str,
    buyer_id: str,
    total_amount: float,
    document_text: str,
    currency: str = "EUR",
    po_id: str | None = None,
    negotiation_session_id: str | None = None,
) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        now = datetime.utcnow().isoformat() + "Z"
        po_id = (po_id or "").strip() or f"PO-{uuid.uuid4().hex[:6].upper()}"

        # purchase_orders table exists in seed, but ensure for safety.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id TEXT PRIMARY KEY,
                supplier_id TEXT,
                buyer_id TEXT,
                total_amount REAL,
                currency TEXT,
                status TEXT,
                document_text TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS po_negotiations (
                po_id TEXT,
                session_id TEXT,
                supplier_id TEXT,
                created_at TEXT
            )
            """
        )

        cur.execute(
            f"""
            INSERT OR REPLACE INTO purchase_orders (id, supplier_id, buyer_id, total_amount, currency, status, document_text, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (po_id, supplier_id, buyer_id, float(total_amount or 0), currency or "EUR", "In Transit", document_text or "", now),
        )

        if negotiation_session_id:
            cur.execute(
                f"""
                INSERT INTO po_negotiations (po_id, session_id, supplier_id, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (po_id, negotiation_session_id, supplier_id, now),
            )

        conn.commit()
        return {"success": True, "po_id": po_id, "supplier_id": supplier_id, "buyer_id": buyer_id}
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        log.exception("create_purchase_order failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def auto_select_supplier_for_line_item(line_item_id: str, top_k: int = 3) -> dict:
    """Deterministically discover + pick best supplier and persist selection.

    Returns a shortlist (up to top_k) plus the chosen supplier and a templated explanation.
    """

    try:
        k = max(int(top_k or 3), 1)
    except Exception:
        k = 3

    discovery = discover_suppliers_for_line_item(line_item_id=line_item_id, top_k=k)
    if not discovery.get("success"):
        return {"success": False, "error": discovery.get("error") or "supplier discovery failed"}

    shortlist = discovery.get("shortlist") or []
    if not shortlist:
        return {
            "success": True,
            "line_item_id": line_item_id,
            "shortlist": [],
            "selected": None,
            "explanation": "No suppliers matched current demand and category.",
        }

    def _to_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return float(default)

    best = max(
        shortlist,
        key=lambda s: (
            _to_float(s.get("fit_score"), 0.0),
            _to_float(s.get("trust_score"), 0.0),
            -_to_float(s.get("base_unit_price"), 1e18),
        ),
    )

    supplier_id = best.get("supplier_id")
    persisted = select_supplier_for_line_item(line_item_id=line_item_id, supplier_id=supplier_id)
    if not persisted.get("success"):
        return {"success": False, "error": persisted.get("error") or "supplier selection persist failed"}

    supplier_name = best.get("supplier_name") or supplier_id
    lead_time_days = best.get("lead_time_days")
    trust_score = _to_float(best.get("trust_score"), 0.0)
    base_unit_price = _to_float(best.get("base_unit_price"), 0.0)
    fit_score = _to_float(best.get("fit_score"), 0.0)

    explanation = (
        f"Selected {supplier_name} (fit_score={fit_score:.3f}) based on lead_time={lead_time_days}d, "
        f"trust={trust_score:.2f}, base_unit_price=€{base_unit_price:,.2f}."
    )

    return {
        "success": True,
        "line_item_id": line_item_id,
        "shortlist": shortlist[:k],
        "selected": {
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "fit_score": fit_score,
            "trust_score": trust_score,
            "base_unit_price": base_unit_price,
            "lead_time_days": lead_time_days,
        },
        "explanation": explanation,
    }


def get_macro_risk_bundle(line_item_id: str, supplier_id: str, buyer_id: str | None = None) -> dict:
    """Combine macro context + supplier risk into one deterministic tool output."""

    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        _ensure_core_tables(cur)

        cur.execute(
            f"""
            SELECT oli.product_category, o.delivery_region
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = {placeholder}
            """,
            (line_item_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        product_category = row["product_category"]
        delivery_region = row["delivery_region"]

        macro = get_macro_context(product_category=product_category, delivery_region=delivery_region)
        risk = assess_supplier_risk(supplier_id=supplier_id, buyer_id=buyer_id)

        macro_urgency = (macro or {}).get("urgency") or "normal"
        risk_level = (risk or {}).get("risk_level") or "medium"

        recommendations = []
        if risk_level == "high":
            recommendations.append("Require HITL approval before committing.")
            recommendations.append("Prefer dual-sourcing or keep a fallback supplier warm.")
        elif risk_level == "medium":
            recommendations.append("Proceed, but add tighter delivery penalties and monitor quality.")
        else:
            recommendations.append("Risk is low; standard terms are acceptable.")

        if macro_urgency == "close_fast":
            recommendations.append("Macro urgency indicates closing quickly; reduce negotiation rounds if needed.")

        summary_bullets = [
            f"Macro urgency: {macro_urgency}.",
            f"Supplier risk: {risk_level} (score={(risk or {}).get('risk_score')}).",
        ]
        if recommendations:
            summary_bullets.append(f"Action: {recommendations[0]}")

        return {
            "success": True,
            "line_item_id": line_item_id,
            "supplier_id": supplier_id,
            "macro": macro,
            "risk": risk,
            "macro_urgency": macro_urgency,
            "risk_level": risk_level,
            "recommendations": recommendations,
            "summary_bullets": summary_bullets,
        }
    except Exception as e:
        log.exception("get_macro_risk_bundle failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def generate_contract_text(
    line_item_id: str,
    supplier_id: str,
    buyer_id: str,
    negotiated_unit_price: float | None,
    currency: str = "EUR",
    payment_terms: str = "Net-30",
    negotiation_session_id: str | None = None,
) -> dict:
    """Generate a deterministic Purchase Order document text from stored order + agreed price."""

    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)

    try:
        _ensure_core_tables(cur)

        cur.execute(
            f"""
            SELECT
              oli.id as line_item_id,
              oli.order_id as order_id,
              oli.product_id as product_id,
              oli.product_name as product_name,
              oli.product_category as product_category,
              oli.quantity as quantity,
              o.delivery_region as delivery_region,
              o.delivery_deadline as delivery_deadline
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = {placeholder}
            """,
            (line_item_id,),
        )
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        cur.execute(f"SELECT id, company_name FROM buyers WHERE id = {placeholder}", (buyer_id,))
        b = cur.fetchone()
        buyer_name = (b["company_name"] if b else None) or buyer_id

        cur.execute(f"SELECT id, company_name FROM suppliers WHERE id = {placeholder}", (supplier_id,))
        s = cur.fetchone()
        supplier_name = (s["company_name"] if s else None) or supplier_id

        qty = int(li["quantity"] or 1)

        unit_price = None
        if negotiated_unit_price is not None:
            try:
                unit_price = float(negotiated_unit_price)
            except Exception:
                unit_price = None

        if unit_price is None:
            # Fallback to catalog price if negotiation price is missing
            cur.execute(
                f"""
                SELECT unit_price
                FROM supplier_products
                WHERE supplier_id = {placeholder} AND LOWER(category) = LOWER({placeholder})
                ORDER BY unit_price ASC
                LIMIT 1
                """,
                (supplier_id, li["product_category"]),
            )
            row = cur.fetchone()
            if row:
                try:
                    v = row.get("unit_price")
                except Exception:
                    v = row["unit_price"]
                if v is not None:
                    unit_price = float(v)

        if unit_price is None:
            return {"success": False, "error": "Missing negotiated_unit_price and no catalog fallback available"}

        po_id = f"PO-{uuid.uuid4().hex[:6].upper()}"
        issued = datetime.utcnow().strftime("%Y-%m-%d")

        product_name = li["product_name"] or "Unknown Item"
        product_id = li["product_id"] or "N/A"
        delivery_region = li["delivery_region"] or "ANY"
        delivery_deadline = li["delivery_deadline"] or "N/A"

        line_total = round(unit_price * qty, 2)
        subtotal = line_total
        taxes = 0.0
        grand_total = round(subtotal + taxes, 2)

        document_text = "\n".join(
            [
                "NEXUS PURCHASE ORDER",
                "=",  # visual separator
                f"PO Number: {po_id}",
                f"Date of Issue: {issued}",
                "",
                "Buyer:",
                f"- ID: {buyer_id}",
                f"- Company: {buyer_name}",
                "",
                "Supplier:",
                f"- ID: {supplier_id}",
                f"- Company: {supplier_name}",
                "",
                "Items:",
                f"- {qty} × {product_name} ({product_id}) @ {currency} {unit_price:,.2f} = {currency} {line_total:,.2f}",
                "",
                f"Subtotal: {currency} {subtotal:,.2f}",
                f"Taxes: {currency} {taxes:,.2f}",
                f"Grand Total: {currency} {grand_total:,.2f}",
                "",
                f"Delivery Region: {delivery_region}",
                f"Delivery By: {delivery_deadline}",
                f"Payment Terms: {payment_terms}",
                "",
                "Terms & Conditions:",
                "- Standard NEXUS Terms apply.",
                "- Late delivery penalty: 2% of total per week (demo).",
                "- Quality issues require replacement or credit (demo).",
                "",
                "Digital Signatures:",
                f"- Buyer: ____________________   Date: {issued}",
                f"- Supplier: __________________  Date: {issued}",
            ]
        )

        return {
            "success": True,
            "po_id": po_id,
            "buyer_id": buyer_id,
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "currency": currency,
            "payment_terms": payment_terms,
            "negotiation_session_id": negotiation_session_id,
            "unit_price": round(unit_price, 2),
            "quantity": qty,
            "total_amount": grand_total,
            "document_text": document_text,
        }

    except Exception as e:
        log.exception("generate_contract_text failed")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
