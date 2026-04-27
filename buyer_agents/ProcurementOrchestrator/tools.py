import json
import uuid
from datetime import date, datetime, timedelta

from db import get_conn
from logger import setup_logger

log = setup_logger("procurement_orchestrator.tools")


def _normalize_specs(specs):
    if isinstance(specs, dict):
        return specs
    if isinstance(specs, str):
        try:
            return json.loads(specs)
        except Exception:
            return {}
    return {}


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


def _ensure_buyer_exists(cur, buyer_id: str):
    """
    Schema requires orders.buyer_id to exist in buyers.
    For demo/dev runs, if the buyer row is missing we auto-create it.
    """
    if not buyer_id or not str(buyer_id).strip():
        buyer_id = "buyer-unknown"
    cur.execute("SELECT id FROM buyers WHERE id = %s", (buyer_id,))
    row = cur.fetchone()
    if row:
        return buyer_id
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        """
        INSERT INTO buyers (id, company_name, country, region, industry, negotiation_style, is_active, registered_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
) -> dict:
    """Create order + line item and resolve best baseline product from catalog."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        buyer_id = _ensure_buyer_exists(cur, buyer_id)
        order_id = f"ord-{uuid.uuid4().hex[:8]}"
        line_item_id = f"li-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        deadline_date = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

        cur.execute(
            """
            INSERT INTO orders
            (id, buyer_id, status, priority, delivery_region, delivery_deadline,
             total_budget_ceiling, negotiation_style, created_at)
            VALUES (%s, %s, 'negotiating', %s, %s, %s, %s, %s, %s)
            """,
            (
                order_id,
                buyer_id,
                priority,
                delivery_region,
                deadline_date,
                max_price * quantity,
                negotiation_style,
                now,
            ),
        )

        cur.execute(
            """
            SELECT product_name, product_category, specs
            FROM supplier_catalog
            WHERE is_available = 1
              AND (
                LOWER(product_name) LIKE LOWER(%s)
                OR LOWER(product_category) LIKE LOWER(%s)
              )
            ORDER BY stock_available DESC, lead_time_days ASC
            LIMIT 1
            """,
            (f"%{product}%", f"%{product}%"),
        )
        best = cur.fetchone()
        resolved_product_name = best["product_name"] if best else product
        product_category = best["product_category"] if best else "unknown"
        key_specs = _normalize_specs(best["specs"]) if best else {}

        cur.execute(
            """
            INSERT INTO order_line_items
            (id, order_id, product_name, product_category, quantity, target_unit_price,
             max_unit_price, agent_instruction, resolved_product_name, key_specs,
             status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'discovering', %s)
            """,
            (
                line_item_id,
                order_id,
                product,
                product_category,
                quantity,
                target_price,
                max_price,
                instruction,
                resolved_product_name,
                json.dumps(key_specs),
                now,
            ),
        )
        conn.commit()
        confidence = 0.85 if best else 0.55
        return {
            "success": True,
            "order_id": order_id,
            "line_item_id": line_item_id,
            "resolved_product_name": resolved_product_name,
            "product_category": product_category,
            "key_specs": key_specs,
            "confidence_score": confidence,
            "ready_for_discovery": bool(best),
        }
    except Exception as e:
        conn.rollback()
        log.error("parse_intent_and_create_order failed: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def discover_suppliers_for_line_item(line_item_id: str, top_k: int = 5) -> dict:
    """Build ranked supplier shortlist for an existing line item."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT oli.id, oli.order_id, oli.product_category, oli.quantity, oli.target_unit_price,
                   o.buyer_id, o.delivery_region, o.delivery_deadline
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = %s
            """,
            (line_item_id,),
        )
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        cur.execute(
            """
            SELECT s.id AS supplier_id, s.name, s.region, s.certifications,
                   sc.product_name, sc.base_unit_price, sc.lead_time_days, sc.stock_available,
                   ts.overall_score AS trust_score,
                   COALESCE(sbr.total_orders, 0) AS prior_orders,
                   COALESCE(sbr.supplier_on_time_rate, 0.5) AS on_time_rate
            FROM suppliers s
            JOIN supplier_catalog sc ON sc.supplier_id = s.id
            LEFT JOIN trust_scores ts ON ts.entity_id = s.id AND ts.entity_type = 'supplier'
            LEFT JOIN supplier_buyer_relationship sbr
                   ON sbr.supplier_id = s.id AND sbr.buyer_id = %s
            WHERE s.is_active = 1
              AND sc.is_available = 1
              AND LOWER(sc.product_category) = LOWER(%s)
              AND sc.stock_available >= %s
            """,
            (li["buyer_id"], li["product_category"], li["quantity"]),
        )
        rows = cur.fetchall()
        if not rows:
            return {
                "success": True,
                "line_item_id": line_item_id,
                "shortlist": [],
                "message": "No suppliers match current demand and category.",
            }

        deadline = _safe_parse_iso_date(li["delivery_deadline"])
        ranked = []
        for row in rows:
            days_left = max((deadline - datetime.utcnow().date()).days, 1)
            lead_fit = 1.0 if row["lead_time_days"] <= days_left else 0.3
            price_fit = 1.0 if row["base_unit_price"] <= li["target_unit_price"] else 0.6
            trust = float(row["trust_score"] or 0.5)
            rel = min(float(row["prior_orders"]) / 5.0, 1.0)
            score = round((0.30 * lead_fit) + (0.25 * price_fit) + (0.30 * trust) + (0.15 * rel), 3)
            ranked.append(
                {
                    "supplier_id": row["supplier_id"],
                    "supplier_name": row["name"],
                    "quoted_product": row["product_name"],
                    "base_unit_price": float(row["base_unit_price"]),
                    "lead_time_days": row["lead_time_days"],
                    "trust_score": trust,
                    "prior_orders": row["prior_orders"],
                    "fit_score": score,
                    "rationale": f"lead_fit={lead_fit}, price_fit={price_fit}, trust={trust:.2f}, relationship={rel:.2f}",
                }
            )

        shortlist = sorted(ranked, key=lambda r: r["fit_score"], reverse=True)[:top_k]
        return {"success": True, "line_item_id": line_item_id, "shortlist": shortlist}
    except Exception as e:
        log.error("discover_suppliers_for_line_item failed: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def get_macro_context(product_category: str, delivery_region: str) -> dict:
    """Get currently active macro signals for category and region."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, signal_type, severity, direction, headline, recommendation, affected_category
            FROM macro_signals
            WHERE valid_until::date >= CURRENT_DATE
              AND (
                LOWER(affected_category) LIKE LOWER(%s)
                OR LOWER(affected_category) LIKE LOWER(%s)
              )
            ORDER BY
              CASE severity WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END DESC,
              created_at DESC
            """,
            (f"%{product_category}%", f"%{delivery_region}%"),
        )
        signals = cur.fetchall()
        formatted = [
            {
                "id": s["id"],
                "type": s["signal_type"],
                "severity": s["severity"],
                "direction": s["direction"],
                "headline": s["headline"],
                "action": s["recommendation"],
            }
            for s in signals
        ]
        urgency = "normal"
        if any(s["severity"] == "high" and s["direction"] == "price_up" for s in formatted):
            urgency = "close_fast"
        return {"success": True, "urgency": urgency, "signals": formatted}
    except Exception as e:
        log.error("get_macro_context failed: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def assess_supplier_risk(supplier_id: str, buyer_id: str) -> dict:
    """Score supplier risk profile for this buyer relationship."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT ts.overall_score, ts.delivery_score, ts.quality_score, ts.supplier_dispute_rate,
                   sbr.dispute_count, sbr.supplier_on_time_rate, sbr.relationship_tier
            FROM suppliers s
            LEFT JOIN trust_scores ts ON ts.entity_id = s.id AND ts.entity_type = 'supplier'
            LEFT JOIN supplier_buyer_relationship sbr
                   ON sbr.supplier_id = s.id AND sbr.buyer_id = %s
            WHERE s.id = %s
            """,
            (buyer_id, supplier_id),
        )
        row = cur.fetchone()
        if not row:
            return {"success": False, "error": f"supplier_id not found: {supplier_id}"}

        trust = float(row["overall_score"] or 0.5)
        delivery = float(row["delivery_score"] or row["supplier_on_time_rate"] or 0.5)
        quality = float(row["quality_score"] or 0.5)
        disputes = float(row["supplier_dispute_rate"] or 0.0)
        dispute_count = int(row["dispute_count"] or 0)

        risk_score = round((0.35 * (1 - trust)) + (0.25 * (1 - delivery)) + (0.20 * (1 - quality)) + (0.20 * disputes), 3)
        level = "low"
        if risk_score >= 0.60:
            level = "high"
        elif risk_score >= 0.35:
            level = "medium"

        blockers = []
        if level == "high":
            blockers.append("require_hitl_before_commit")
        if dispute_count >= 2:
            blockers.append("high_historical_dispute_volume")

        return {
            "success": True,
            "supplier_id": supplier_id,
            "risk_level": level,
            "risk_score": risk_score,
            "blockers": blockers,
            "dimensions": {
                "trust": trust,
                "delivery": delivery,
                "quality": quality,
                "disputes": disputes,
            },
        }
    except Exception as e:
        log.error("assess_supplier_risk failed: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def create_negotiation_strategy(
    line_item_id: str,
    supplier_id: str,
    macro_urgency: str = "normal",
    risk_level: str = "medium",
) -> dict:
    """Produce a buyer-safe negotiation strategy and suggested offer ladder."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT oli.target_unit_price, oli.max_unit_price, oli.quantity, o.buyer_id
            FROM order_line_items oli
            JOIN orders o ON o.id = oli.order_id
            WHERE oli.id = %s
            """,
            (line_item_id,),
        )
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        cur.execute(
            """
            SELECT base_unit_price, lead_time_days
            FROM supplier_catalog
            WHERE supplier_id = %s
            ORDER BY base_unit_price ASC
            LIMIT 1
            """,
            (supplier_id,),
        )
        quote = cur.fetchone()
        if not quote:
            return {"success": False, "error": f"no catalog quote found for supplier_id: {supplier_id}"}

        market = float(quote["base_unit_price"])
        target = float(li["target_unit_price"])
        max_price = float(li["max_unit_price"])

        open_offer = round(min(target, market * 0.95), 2)
        mid_offer = round(min(max(target + 0.03, market * 0.98), max_price - 0.02), 2)
        walkaway = round(max_price, 2)
        if macro_urgency == "close_fast":
            mid_offer = round(min(max_price - 0.01, max(mid_offer, market)), 2)

        escalate_hitl = risk_level == "high" or walkaway < market
        return {
            "success": True,
            "line_item_id": line_item_id,
            "supplier_id": supplier_id,
            "strategy": {
                "open_offer": open_offer,
                "counter_offer": mid_offer,
                "walkaway_price_internal_only": walkaway,
                "anchor_arguments": [
                    "historical relationship value",
                    "volume commitment",
                    "delivery reliability expectations",
                ],
                "hitl_required": escalate_hitl,
                "hitl_reason": "high_risk_or_price_conflict" if escalate_hitl else None,
            },
            "safety_note": "Never disclose walkaway_price_internal_only to supplier.",
        }
    except Exception as e:
        log.error("create_negotiation_strategy failed: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def select_supplier_for_line_item(line_item_id: str, supplier_id: str) -> dict:
    """Persist buyer-selected supplier on the line item."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, order_id FROM order_line_items WHERE id = %s", (line_item_id,))
        li = cur.fetchone()
        if not li:
            return {"success": False, "error": f"line_item_id not found: {line_item_id}"}

        cur.execute("SELECT id, name FROM suppliers WHERE id = %s AND is_active = 1", (supplier_id,))
        s = cur.fetchone()
        if not s:
            return {"success": False, "error": f"supplier_id not found or inactive: {supplier_id}"}

        cur.execute(
            """
            UPDATE order_line_items
            SET supplier_id = %s,
                status = 'rfq_sent'
            WHERE id = %s
            """,
            (supplier_id, line_item_id),
        )
        conn.commit()
        return {
            "success": True,
            "line_item_id": line_item_id,
            "order_id": li["order_id"],
            "supplier_id": supplier_id,
            "supplier_name": s["name"],
            "status_updated_to": "rfq_sent",
        }
    except Exception as e:
        conn.rollback()
        log.error("select_supplier_for_line_item failed: %s", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

