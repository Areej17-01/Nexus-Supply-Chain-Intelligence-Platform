"""
Supplier Quote Agent Tools
Tools that a supplier agent uses to generate quotes, check inventory, and fulfill RFQs
"""

import json
from datetime import datetime, timedelta
from nexus.core.db import get_db_conn as get_conn
from nexus.core.logger import setup_logger

import uuid

log = setup_logger("supplier.quote_tools")


def _is_sqlite_conn(conn) -> bool:
    return conn.__class__.__module__.startswith("sqlite3")


def _ph(conn) -> str:
    return "?" if _is_sqlite_conn(conn) else "%s"


def get_supplier_catalog(supplier_id: str) -> dict:

    log.info("[TOOL] get_supplier_catalog supplier_id=%s", supplier_id)

    """
    Retrieve the supplier's product catalog from the database.
    
    Args:
        supplier_id: The supplier's unique ID (e.g., 'supplier-001')
    
    Returns:
        Dictionary with products, prices, stock levels, and certifications
    """
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    
    try:
        # Get supplier info
        cur.execute(
            f"""
            SELECT id, company_name, country, region, certifications, 
                   trust_score, negotiation_style
            FROM suppliers
            WHERE id = {placeholder}
            """,
            (supplier_id,),
        )
        
        supplier = cur.fetchone()
        if not supplier:
            return {"error": f"Supplier {supplier_id} not found"}
        
        # Get supplier's catalog
        cur.execute(
            f"""
            SELECT product_id, product_name, category, unit_price, 
                   stock_quantity, lead_time_days, certifications_required
            FROM supplier_products
            WHERE supplier_id = {placeholder}
            """,
            (supplier_id,),
        )

        
        products = cur.fetchall()
        
        return {
            "supplier_id": supplier_id,
            "company_name": supplier["company_name"],
            "region": supplier["region"],
            "country": supplier["country"],
            "certifications": supplier["certifications"],
            "trust_score": supplier["trust_score"],
            "products": [
                {
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "category": p["category"],
                    "unit_price": p["unit_price"],
                    "stock_quantity": p["stock_quantity"],
                    "lead_time_days": p["lead_time_days"],
                    "certifications_required": p["certifications_required"]
                }
                for p in products
            ]
        }
    
    except Exception as e:
        log.exception("[TOOL_ERROR] get_supplier_catalog failed supplier_id=%s", supplier_id)
        return {"error": str(e)}




    finally:
        conn.close()


def check_inventory(supplier_id: str, product_id: str, quantity_needed: int) -> dict:
    log.info("[TOOL] check_inventory supplier_id=%s product_id=%s quantity_needed=%s", supplier_id, product_id, quantity_needed)

    """
    Check if a supplier has enough inventory for a product.
    
    Args:
        supplier_id: Supplier's unique ID
        product_id: Product ID
        quantity_needed: How many units are needed
    
    Returns:
        Dictionary with availability status and options
    """
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    
    try:
        cur.execute(
            f"""
            SELECT product_name, stock_quantity, lead_time_days, unit_price
            FROM supplier_products
            WHERE supplier_id = {placeholder} AND product_id = {placeholder}
            """,
            (supplier_id, product_id),
        )

        
        product = cur.fetchone()
        
        if not product:
            return {
                "available": False,
                "reason": "Product not found in supplier catalog"
            }
        
        stock = product["stock_quantity"]
        lead_time = product["lead_time_days"]
        
        if stock >= quantity_needed:
            return {
                "available": True,
                "can_fulfill_immediately": True,
                "stock_available": stock,
                "quantity_needed": quantity_needed,
                "lead_time_days": 3,  # Standard delivery if in stock
                "product_name": product["product_name"]
            }
        elif stock > 0:
            # Partial stock
            return {
                "available": True,
                "can_fulfill_immediately": False,
                "stock_available": stock,
                "quantity_needed": quantity_needed,
                "quantity_short": quantity_needed - stock,
                "lead_time_days": lead_time,
                "product_name": product["product_name"],
                "note": f"Can deliver {stock} units immediately, rest in {lead_time} days"
            }
        else:
            return {
                "available": False,
                "can_fulfill_immediately": False,
                "stock_available": 0,
                "quantity_needed": quantity_needed,
                "lead_time_days": lead_time,
                "product_name": product["product_name"],
                "note": f"Out of stock. Can deliver in {lead_time} days"
            }
    
    except Exception as e:
        log.exception("[TOOL_ERROR] check_inventory failed supplier_id=%s product_id=%s", supplier_id, product_id)
        return {"error": str(e)}




    finally:
        conn.close()


def calculate_quote(
    supplier_id: str,
    items: list,  # [{"product_id": "...", "quantity": int}, ...]
    buyer_id: str = None,
    negotiation_style: str = "balanced",
    bulk_discount_tier: str = "standard"
) -> dict:
    log.info("[TOOL] calculate_quote supplier_id=%s buyer_id=%s items=%s negotiation_style=%s bulk_discount_tier=%s", supplier_id, buyer_id, len(items or []), negotiation_style, bulk_discount_tier)

    """
    Calculate a quote for the requested items.
    Applies volume discounts, considers buyer relationship, and calculates totals.
    
    Args:
        supplier_id: Supplier's ID
        items: List of items with product_id and quantity
        buyer_id: Buyer's ID (used for relationship discounts)
        negotiation_style: Supplier's negotiation approach
        bulk_discount_tier: Bulk discount level (standard, volume, enterprise)
    
    Returns:
        Quote object with line items, totals, and terms
    """
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    
    try:

        quote_id = f"quote-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat() + "Z"
        quote_valid_until = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        
        line_items = []
        total_amount = 0.0
        
        # Process each requested item
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            
            cur.execute(
                f"""
                SELECT product_name, category, unit_price, stock_quantity, 
                       lead_time_days
                FROM supplier_products
                WHERE supplier_id = {placeholder} AND product_id = {placeholder}
                """,
                (supplier_id, product_id),
            )

            
            product = cur.fetchone()
            
            if not product:
                continue
            
            unit_price = product["unit_price"]
            
            # Apply volume discounts
            if quantity >= 1000:
                discount_rate = 0.15  # 15% for 1000+
            elif quantity >= 500:
                discount_rate = 0.10  # 10% for 500+
            elif quantity >= 100:
                discount_rate = 0.05  # 5% for 100+
            else:
                discount_rate = 0.0
            
            discounted_price = unit_price * (1 - discount_rate)
            line_total = discounted_price * quantity
            total_amount += line_total
            
            line_items.append({
                "product_id": product_id,
                "product_name": product["product_name"],
                "category": product["category"],
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_rate": discount_rate,
                "discounted_unit_price": discounted_price,
                "line_total": line_total,
                "lead_time_days": product["lead_time_days"],
                "in_stock": product["stock_quantity"] >= quantity
            })
        
        # Get supplier info for quote
        cur.execute(
            f"""
            SELECT company_name, country, region, certifications
            FROM suppliers
            WHERE id = {placeholder}
            """,
            (supplier_id,),
        )

        
        supplier = cur.fetchone()
        
        # Check buyer history for relationship discount
        relationship_discount = 0.0
        if buyer_id:
            cur.execute(
                f"""
                SELECT COUNT(*) as previous_orders
                FROM orders
                WHERE buyer_id = {placeholder} AND status IN ('completed', 'shipped')
                """,
                (buyer_id,),
            )

            
            order_count = cur.fetchone()["previous_orders"]
            if order_count >= 3:
                relationship_discount = 0.02  # 2% loyalty discount
        
        # Apply relationship discount
        if relationship_discount > 0:
            total_amount *= (1 - relationship_discount)
        
        # Add payment terms and conditions
        payment_terms = {
            "standard": "Net-30",
            "aggressive": "Net-15",
            "quality_first": "Net-45"
        }
        
        quote_data = {
            "quote_id": quote_id,
            "supplier_id": supplier_id,
            "supplier_name": supplier["company_name"],
            "supplier_region": supplier["region"],
            "supplier_country": supplier["country"],
            "supplier_certifications": supplier["certifications"],
            "buyer_id": buyer_id or "anonymous",
            "line_items": line_items,
            "subtotal": total_amount,
            "payment_terms": payment_terms.get(negotiation_style, "Net-30"),
            "currency": "EUR",
            "created_at": now,
            "valid_until": quote_valid_until,
            "relationship_discount_applied": relationship_discount > 0,
            "discount_amount": total_amount * relationship_discount if relationship_discount > 0 else 0,
            "notes": f"Quote valid for 7 days. Bulk discounts applied for quantities > 100 units.",
            "status": "pending_acceptance"
        }
        
        return quote_data
    
    except Exception as e:
        log.exception("[TOOL_ERROR] calculate_quote failed supplier_id=%s buyer_id=%s", supplier_id, buyer_id)
        return {"error": str(e)}


    finally:
        conn.close()


def validate_buyer_requirements(
    supplier_id: str,
    required_certifications: list,
    delivery_region: str,
    lead_time_days: int
) -> dict:
    log.info("[TOOL] validate_buyer_requirements supplier_id=%s delivery_region=%s lead_time_days=%s required_certifications=%s", supplier_id, delivery_region, lead_time_days, required_certifications)

    """
    Validate if the supplier meets the buyer's requirements.
    
    Args:
        supplier_id: Supplier's ID
        required_certifications: List of required certs (e.g., ['CE', 'ISO9001'])
        delivery_region: Target delivery region
        lead_time_days: Required lead time
    
    Returns:
        Validation results with compliance status
    """
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    
    try:

        cur.execute(
            f"""
            SELECT certifications, region, country
            FROM suppliers
            WHERE id = {placeholder}
            """,
            (supplier_id,),
        )

        
        supplier = cur.fetchone()
        
        if not supplier:
            return {"error": "Supplier not found"}
        
        supplier_certs = supplier["certifications"] or []
        
        # Check certifications
        missing_certs = [
            cert for cert in required_certifications 
            if cert not in supplier_certs
        ]
        
        # Check region compatibility
        region_match = supplier["region"] == delivery_region or delivery_region == "ANY"
        
        # Check lead time (assume standard lead time is 14 days)
        can_meet_deadline = lead_time_days >= 14
        
        validation = {
            "supplier_id": supplier_id,
            "meets_requirements": len(missing_certs) == 0 and region_match and can_meet_deadline,
            "certifications_met": len(missing_certs) == 0,
            "required_certifications": required_certifications,
            "missing_certifications": missing_certs,
            "region_compatible": region_match,
            "supplier_region": supplier["region"],
            "requested_region": delivery_region,
            "can_meet_deadline": can_meet_deadline,
            "supplier_lead_time": 14  # Default
        }
        
        return validation
    
    except Exception as e:
        log.exception("[TOOL_ERROR] validate_buyer_requirements failed supplier_id=%s", supplier_id)
        return {"error": str(e)}


    finally:
        conn.close()


def save_quote_to_db(supplier_id: str, quote_data: dict, order_id: str = None) -> dict:
    log.info("[TOOL] save_quote_to_db supplier_id=%s quote_id=%s order_id=%s", supplier_id, quote_data.get("quote_id"), order_id)

    """
    Save the generated quote to the database for tracking and negotiation.
    
    Args:
        supplier_id: Supplier's ID
        quote_data: Quote dictionary from calculate_quote()
        order_id: Optional order ID to link quote to order
    
    Returns:
        Confirmation with quote_id
    """
    conn = get_conn()
    cur = conn.cursor()
    placeholder = _ph(conn)
    
    try:

        cur.execute(
            f"""
            INSERT INTO quotes
            (id, supplier_id, order_id, line_items, total_amount,
             payment_terms, currency, status, created_at, valid_until)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 'pending', {placeholder}, {placeholder})
            """,
            (
                quote_data["quote_id"],
                supplier_id,
                order_id,
                json.dumps(quote_data["line_items"]),
                quote_data["subtotal"],
                quote_data["payment_terms"],
                quote_data["currency"],
                quote_data["created_at"],
                quote_data["valid_until"],
            ),
        )

        
        conn.commit()
        
        return {
            "success": True,
            "quote_id": quote_data["quote_id"],
            "message": "Quote saved successfully"
        }
    
    except Exception as e:
        conn.rollback()
        log.exception("[TOOL_ERROR] save_quote_to_db failed supplier_id=%s quote_id=%s", supplier_id, quote_data.get("quote_id"))
        return {"success": False, "error": str(e)}

    finally:
        conn.close()
