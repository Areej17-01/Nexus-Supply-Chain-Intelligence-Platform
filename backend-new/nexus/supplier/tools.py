from __future__ import annotations

import json
from datetime import datetime, timedelta

from nexus.buyer.tools import call_openrouter
from nexus.database import Negotiation, Supplier, get_db_session
from nexus.protocols.schemas import CounterOfferMessage, NegotiationResponse, QuoteResponse, RFQMessage
from nexus.supplier.pricing import calculate_unit_price, get_base_and_floor
from nexus.supplier.prompts import SUPPLIER_NEGOTIATION_PROMPT, SUPPLIER_RATIONALE_PROMPT


def handle_rfq(rfq: dict) -> dict:
    msg = RFQMessage(**rfq)
    with get_db_session() as db:
        supplier = db.query(Supplier).filter(Supplier.id == msg.supplier_id).first()
        if not supplier:
            raise ValueError("Supplier not found")

        category = msg.items[0].category
        quantity = msg.items[0].quantity
        base_price, _ = get_base_and_floor(supplier.base_price_map, supplier.price_floor_map, category)
        unit_price, _ = calculate_unit_price(base_price, quantity)
        total_price = round(unit_price * quantity, 2)

        quote = QuoteResponse(
            type="quote",
            negotiation_id=msg.negotiation_id,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            unit_price=unit_price,
            total_price=total_price,
            lead_time_days=supplier.lead_time_days,
            certifications=json.loads(supplier.certifications or "[]") if supplier.certifications else [],
            valid_until=(datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            rationale="",
        )
        return quote.model_dump()


async def generate_winner_rationale(unit_price: float, base_price: float, discount: float, product: str) -> str:
    try:
        text = await call_openrouter(
            SUPPLIER_RATIONALE_PROMPT,
            f"Unit price €{unit_price} for {product}. Base price €{base_price}. Discount {int(discount*100)}%.",
        )
        return text.strip()
    except Exception:
        return f"Quote of €{unit_price}/unit includes {int(discount*100)}% volume discount off base price of €{base_price}/unit."


async def handle_counter_offer(counter: dict) -> dict:
    msg = CounterOfferMessage(**counter)
    with get_db_session() as db:
        neg = db.query(Negotiation).filter(Negotiation.id == msg.negotiation_id).first()
        if not neg:
            raise ValueError("Negotiation not found")
        supplier = db.query(Supplier).filter(Supplier.id == neg.supplier_id).first()
        if not supplier:
            raise ValueError("Supplier not found")

        category = neg.product_category or "sensors"
        base_price, price_floor = get_base_and_floor(supplier.base_price_map, supplier.price_floor_map, category)
        reduction = 0.0
        if (neg.quantity or 0) >= 1000:
            reduction = 0.10
        elif (neg.quantity or 0) >= 500:
            reduction = 0.07
        elif (neg.quantity or 0) >= 100:
            reduction = 0.03
        price_floor = round(price_floor * (1 - reduction), 2)


    buyer_offer = msg.buyer_price
    if buyer_offer >= price_floor:
        accepted = True
        counter_price = None
    else:
        accepted = False
        mid = (price_floor + buyer_offer) / 2
        counter_price = max(round(mid, 2), price_floor)

    try:
        rationale = await call_openrouter(
            SUPPLIER_NEGOTIATION_PROMPT,
            f"Accepted={accepted}. Buyer offer €{buyer_offer}. Counter {counter_price}. Floor {price_floor}.",
        )
        rationale = rationale.strip()
    except Exception:
        if accepted:
            rationale = f"Deal confirmed at €{buyer_offer}/unit."
        else:
            rationale = f"€{buyer_offer} is below our cost margin. Best we can do is €{counter_price}/unit."

    response = NegotiationResponse(
        type="negotiation_response",
        negotiation_id=msg.negotiation_id,
        supplier_id=supplier.id,
        accepted=accepted,
        counter_price=counter_price,
        rationale=rationale,
        final=accepted,
    )
    return response.model_dump()


async def route_message(message_json: str) -> dict:
    data = json.loads(message_json)
    msg_type = data.get("type")
    if msg_type == "rfq":
        return handle_rfq(data)
    if msg_type == "counter_offer":
        return await handle_counter_offer(data)
    return {"error": "Unknown message type"}
