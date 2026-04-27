import json
from datetime import datetime,timedelta
# from google.adk.tools import tool
from db import get_conn
import uuid
from logger import setup_logger

log = setup_logger("intent_parser.tools")

def extract_and_save_order(
    buyer_id: str,
    product: str,
    quantity: int,
    target_price: float,
    max_price: float,
    delivery_region: str,
    deadline_days: int,
    instruction: str = "",
    priority: str = "standard",
    negotiation_style: str = "balanced"
) -> dict:
    """
    Save the buyer's raw order request into the database.
    Call this FIRST before any product resolution happens.
    Creates a new order and order_line_item from the buyer's chat input.
 
    Args:
        buyer_id: Authenticated buyer ID e.g. 'buyer-001'
        product: Raw product description e.g. 'temperature sensor'
        quantity: How many units needed
        target_price: Buyer's desired price per unit in EUR
        max_price: Buyer's absolute maximum per unit in EUR (never share with supplier)
        delivery_region: e.g. 'EU', 'North America', 'Asia'
        deadline_days: Days until delivery needed
        instruction: Buyer behavioral note e.g. 'close fast'
        priority: 'standard', 'urgent', or 'critical'
        negotiation_style: 'balanced', 'aggressive', or 'quality_first'
 
    Returns:
        Dictionary with created order_id and line_item_id
    """
    conn = get_conn()
    cur = conn.cursor()
 
    try:
        log.info(f"[TOOL 1] extract_and_save_order | buyer={buyer_id} product='{product}' qty={quantity} target={target_price} max={max_price} region={delivery_region}")

        order_id = f"ord-{uuid.uuid4().hex[:8]}"
        line_item_id = f"li-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        deadline_date = (datetime.utcnow() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")
 
        cur.execute("""
            INSERT INTO orders
            (id, buyer_id, status, priority, delivery_region, delivery_deadline,
             total_budget_ceiling, negotiation_style, created_at)
            VALUES (%s, %s, 'negotiating', %s, %s, %s, %s, %s, %s)
        """, (
            order_id, buyer_id, priority, delivery_region,
            deadline_date, max_price * quantity, negotiation_style, now
        ))
 
        cur.execute("""
            INSERT INTO order_line_items
            (id, order_id, product_name, quantity, target_unit_price,
             max_unit_price, agent_instruction, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s)
        """, (
            line_item_id, order_id, product, quantity,
            target_price, max_price, instruction, now
        ))
 
        conn.commit()
        log.info(f"[TOOL 1] Order saved | order_id={order_id} line_item_id={line_item_id}")

        return {
            "success": True,
            "order_id": order_id,
            "line_item_id": line_item_id,
            "message": "Order created. Proceed to product resolution."
        }
 
    except Exception as e:
        log.error(f"[TOOL 1] DB error | {str(e)}")

        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
 

def lookup_product_catalog(product_name:str,category_hint:str="") -> dict:
    """
    Search the supplier catalog for products matching the buyer's description.
    Use this to resolve vague product names into specific technical products.
 
    Args:
        product_name: Raw product name from buyer e.g. 'temperature sensor'
        category_hint: Optional category to narrow search e.g. 'temperature_sensors'
 
    Returns:
        Dictionary with matched products and their specs
    """
    log.info(f"[TOOL 2] lookup_product_catalog | product='{product_name}' hint='{category_hint}'")

    conn = get_conn()
    cur = conn.cursor()

    base_query = """
    SELECT DISTINCT 
        product_name,
        product_category,
        specs,
        base_unit_price,
        currency,
        MIN(lead_time_days) as min_lead_time,
        SUM(stock_available) as total_stock
    FROM supplier_catalog
    WHERE is_available = 1
        AND(
            LOWER(product_name) LIKE LOWER(%s)
            OR LOWER(product_category) LIKE LOWER(%s)
        )
        {category_filter}
        GROUP BY product_name, product_category, specs, base_unit_price, currency
        ORDER BY total_stock DESC
        LIMIT 8
    """ 
    params = [f"%{product_name}%", f"%{product_name}%"]


    if category_hint:
        query = base_query.format(category_filter = "AND LOWER(product_category) LIKE LOWER(%s)")
        params.append(f"%{category_hint}%")
    else:
        query = base_query.format(category_filter="")
    
    cur.execute(query,params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {
            "found": False,
            "matches": [],
            "message": f"No catalog entries found for '{product_name}'."
        }
    
    matches = []
    for row in rows:
        specs = row["specs"]
        if isinstance(specs, str):
            try:
                specs = json.loads(specs)
            except Exception:
                specs = {}
        matches.append({
            "product_name": row["product_name"],
            "product_category": row["product_category"],
            "specs": specs,
            "price_eur": row["base_unit_price"],
            "min_lead_time_days": row["min_lead_time"],
            "total_stock": row["total_stock"]
        })
    log.info(f"[TOOL 2] Found {len(matches)} matches")
    log.debug(f"[TOOL 2] Matches: {json.dumps(matches, indent=2)}")
    return {"found": True, "match_count": len(matches), "matches": matches}



def get_category_certifications(product_category: str, delivery_region: str) -> dict:
    log.info(f"[TOOL 3] get_category_certifications | category={product_category} region={delivery_region}")

    """
    Get certifications commonly required for a product category and delivery region.
    Use this when buyer hasn't specified certifications.
 
    Args:
        product_category: e.g. 'temperature_sensors'
        delivery_region: e.g. 'EU', 'North America', 'Asia'
 
    Returns:
        Dictionary with required and optional certifications
    """
    conn = get_conn()
    cur = conn.cursor()
 
    cur.execute("""
        SELECT certifications
        FROM suppliers
        WHERE is_active = 1
          AND LOWER(categories) LIKE LOWER(%s)
    """, (f"%{product_category}%",))
 
    rows = cur.fetchall()
    conn.close()
 
    if not rows:
        return {
            "product_category": product_category,
            "required_certifications": [],
            "optional_certifications": [],
            "note": "No supplier data for this category"
        }
 
    all_certs = []
    for row in rows:
        certs = row["certifications"]
        if isinstance(certs, str):
            try:
                certs = json.loads(certs)
            except Exception:
                certs = []
        all_certs.extend(certs)
 
    cert_freq = {}
    for cert in all_certs:
        cert_freq[cert] = cert_freq.get(cert, 0) + 1
 
    total = len(rows)
    required = [c for c, count in cert_freq.items() if count / total >= 0.6]
    optional = [c for c, count in cert_freq.items() if 0.3 <= count / total < 0.6]
 
    for cert in {"EU": ["CE", "RoHS"], "North America": ["UL"], "Asia": []}.get(delivery_region, []):
        if cert not in required:
            required.append(cert)
    log.info(f"[TOOL 3] Required certs: {required} | Optional: {optional}")
 
    return {
        "product_category": product_category,
        "delivery_region": delivery_region,
        "required_certifications": required,
        "optional_certifications": optional,
        "note": f"Based on {total} suppliers carrying this category"
    }
 
 
# ------------------------------------------------------------------
# TOOL 4: validate_bom_completeness
# Pure logic — checks if parsed BOM has enough info to send RFQs
# ------------------------------------------------------------------
def validate_bom_completeness(
    resolved_product_name: str,
    product_category: str,
    quantity: int,
    target_unit_price: float,
    max_unit_price: float,
    delivery_region: str,
    deadline_days: int,
    key_specs: str,
    required_certifications: str
) -> dict:
    log.info(f"[TOOL 4] validate_bom_completeness | product='{resolved_product_name}' qty={quantity}")

    """
    Validate whether the parsed BOM is complete enough to send RFQs.
    Use this after resolving the product.
 
    Args:
        resolved_product_name: Specific product name after resolution
        product_category: Resolved product category
        quantity: Order quantity
        target_unit_price: Buyer target price per unit
        max_unit_price: Buyer absolute maximum (never share with supplier)
        delivery_region: Where goods need to be delivered
        deadline_days: Days until delivery deadline
        key_specs: JSON string e.g. '{"resistance":"10k"}'
        required_certifications: JSON string e.g. '["CE","RoHS"]'
 
    Returns:
        Dictionary with ready_for_rfq, confidence_score, missing fields
    """
    missing = []
    warnings = []
    confidence = 1.0
 
    if not resolved_product_name or not resolved_product_name.strip():
        missing.append("resolved_product_name")
        confidence -= 0.4
 
    if not product_category:
        missing.append("product_category")
        confidence -= 0.2
 
    if not quantity or quantity <= 0:
        missing.append("quantity")
        confidence -= 0.2
 
    if not target_unit_price or target_unit_price <= 0:
        missing.append("target_unit_price")
        confidence -= 0.1
 
    if not max_unit_price or max_unit_price <= target_unit_price:
        missing.append("max_unit_price must be above target_unit_price")
        confidence -= 0.1
 
    if not delivery_region:
        missing.append("delivery_region")
        confidence -= 0.1
 
    try:
        specs = json.loads(key_specs) if key_specs else {}
        if not specs:
            warnings.append("key_specs empty — suppliers may ask for clarification")
            confidence -= 0.15
    except Exception:
        warnings.append("key_specs not valid JSON")
        confidence -= 0.1
 
    try:
        certs = json.loads(required_certifications) if required_certifications else []
        if not certs:
            warnings.append("required_certifications empty")
            confidence -= 0.05
    except Exception:
        warnings.append("required_certifications not valid JSON")
        confidence -= 0.05
 
    if deadline_days and deadline_days < 7:
        warnings.append(f"deadline_days={deadline_days} is very tight")
 
    confidence = round(max(0.0, min(1.0, confidence)), 2)
    ready = len(missing) == 0 and confidence >= 0.70
    log.info(f"[TOOL 4] Result: {ready} | confidence={confidence} | missing={missing}")

 
    return {
        "ready_for_rfq": ready,
        "confidence_score": confidence,
        "missing_fields": missing,
        "warnings": warnings,
        "verdict": "PROCEED" if ready else "NEEDS_CLARIFICATION"
    }
 
 
# ------------------------------------------------------------------
# TOOL 5: save_parsed_bom
# Writes resolved BOM back to order_line_items
# ------------------------------------------------------------------
def save_parsed_bom(
    line_item_id: str,
    resolved_product_name: str,
    product_category: str,
    key_specs: str,
    required_certifications: str,
    intent_confidence_score: float
) -> dict:
    log.info(f"[TOOL 5] save_parsed_bom | line_item_id={line_item_id} confidence={intent_confidence_score}")
    """
    Save the resolved BOM fields to order_line_items.
    Call ONLY after validate_bom_completeness returns ready_for_rfq = true.
 
    Args:
        line_item_id: order_line_items.id to update
        resolved_product_name: Resolved specific product name
        product_category: Resolved category
        key_specs: JSON string of technical specs
        required_certifications: JSON string of cert list
        intent_confidence_score: Confidence score from validation
 
    Returns:
        Dictionary with success status
    """
    conn = get_conn()
    cur = conn.cursor()
 
    try:
        cur.execute("""
            UPDATE order_line_items
            SET
                resolved_product_name = %s,
                product_category = %s,
                key_specs = %s,
                required_certifications = %s,
                intent_confidence_score = %s,
                status = 'discovering'
            WHERE id = %s
        """, (
            resolved_product_name,
            product_category,
            key_specs,
            required_certifications,
            intent_confidence_score,
            line_item_id
        ))
 
        conn.commit()
 
        if cur.rowcount == 0:
            log.info(f"[TOOL 5] success: False, error No line item found with id {line_item_id}")
            return {"success": False, "error": f"No line item found with id '{line_item_id}'"}


        log.info(f"[TOOL 5] BOM saved | status=discovering found with id {line_item_id}")
        return {
            "success": True,
            "line_item_id": line_item_id,
            "status_updated_to": "discovering",
            "message": "BOM saved. Ready for Supplier Discovery Agent."
        }
 
    except Exception as e:
        log.error(f"[TOOL 5] Save failed | {str(e)}")
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()