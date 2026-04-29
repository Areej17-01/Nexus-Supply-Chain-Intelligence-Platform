from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import uuid
from datetime import datetime
from typing import List

import httpx
from fastapi import HTTPException

from nexus.buyer.prompts import PARSER_PROMPT
from nexus.buyer.tools import call_openrouter_json
from nexus.config import A2A_SUPPLIER_URL
from nexus.contracts.generator import generate_contract
from nexus.database import Message, Negotiation, Supplier, get_db_session, create_expiry
from nexus.protocols.schemas import (
    BOM,
    CounterOfferMessage,
    ProcurementRequest,
    ProcurementResult,
    QuoteResponse,
    RFQMessage,
)
from nexus.rl.bandit import choose_discount, record_outcome
from nexus.rl.updater import compute_reward, update_scores

MAX_ROUNDS = 3
EPSILON = 0.10

logger = logging.getLogger("nexus.procurement")


async def parse_procurement_request(req: ProcurementRequest) -> BOM:
    try:
        payload = await call_openrouter_json(PARSER_PROMPT, req.request)
        logger.info("parse_procurement_request request=%s", req.request)
        logger.info("parse_procurement_request payload=%s", payload)
        if not payload:
            raise ValueError("JSON parse failed")
        bom = BOM(**payload)
        if req.destination_region:
            bom.destination_region = req.destination_region
        if req.budget is not None:
            bom.budget = req.budget
        if req.deadline_days:
            bom.deadline_days = req.deadline_days
        return bom
    except Exception as exc:
        logger.exception("parse_procurement_request error=%s", repr(exc))
        raise HTTPException(status_code=400, detail="Could not parse procurement request. Please be more specific.")


def _get_budget_per_unit(bom: BOM) -> float | None:
    if not bom.budget:
        return None
    qty = bom.items[0].quantity if bom.items else 1
    return float(bom.budget) / max(qty, 1)


def discover_suppliers(bom: BOM, limit: int = 5) -> List[Supplier]:
    with get_db_session() as db:
        suppliers = db.query(Supplier).all()
        scored = []
        VALID_CATEGORIES = {"sensors", "motors", "cables", "connectors", "displays", "batteries", "other"}
        raw_category = (bom.items[0].category if bom.items else "other").lower().rstrip("s")
        category = next((c for c in VALID_CATEGORIES if c.rstrip("s") == raw_category), bom.items[0].category.lower() if bom.items else "other")
        budget_per_unit = _get_budget_per_unit(bom)
        capable = []
        for s in suppliers:
            try:
                caps = json.loads(s.capabilities or "[]")
            except Exception:
                caps = []
            if category.lower() in [c.lower() for c in caps] or not caps:
                capable.append(s)
        suppliers = capable or suppliers  # fallback to all if none match

        for s in suppliers:
            try:
                base_map = json.loads(s.base_price_map or "{}")
            except Exception:
                base_map = {}
            base_price = float(base_map.get(category, base_map.get("default", 0.0)))
            price_fit = (
                1.0 - min(base_price / budget_per_unit, 1.0)
                if budget_per_unit
                else 0.5
            )
            lead_fit = 1.0 - min((s.lead_time_days or 0) / max(bom.deadline_days, 1), 1.0)
            fit_score = (0.35 * lead_fit) + (0.35 * float(s.trust_score or 0.0)) + (0.30 * price_fit)
            scored.append((fit_score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        shortlisted = [s for _, s in scored[:limit]]
        logger.info(
            "discover_suppliers found=%d shortlisted=%d ids=%s",
            len(suppliers),
            len(shortlisted),
            [s.id for s in shortlisted],
        )
        return shortlisted


async def send_a2a_message(payload: dict) -> dict:
    supplier_id = payload.get("supplier_id") or payload.get("supplierId")
    msg_type = payload.get("type")
    try:
        logger.info("A2A send type=%s supplier_id=%s", msg_type, supplier_id)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                A2A_SUPPLIER_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "messageId": str(uuid.uuid4()),
                            "contextId": str(uuid.uuid4()),
                            "parts": [{"kind": "text", "text": json.dumps(payload)}],
                        }
                    },
                },
            )
            resp.raise_for_status()
            logger.info(
                "A2A response ok type=%s supplier_id=%s status=%s",
                msg_type,
                supplier_id,
                resp.status_code,
            )
            return resp.json()
    except httpx.TimeoutException:
        logger.warning("A2A timeout type=%s supplier_id=%s", msg_type, supplier_id)
        raise
    except httpx.HTTPStatusError as exc:
        logger.error(
            "A2A http error type=%s supplier_id=%s status=%s body=%s",
            msg_type,
            supplier_id,
            exc.response.status_code if exc.response else None,
            exc.response.text if exc.response else None,
        )
        raise
    except Exception:
        logger.exception("A2A error type=%s supplier_id=%s", msg_type, supplier_id)
        raise


def _extract_text(payload: dict) -> str:
    def _text_from_parts(parts: list) -> str:
        for p in parts or []:
            if isinstance(p, dict) and p.get("kind") == "text" and p.get("text"):
                return p["text"]
            if isinstance(p, dict) and p.get("text"):
                return p["text"]
        return ""

    # JSON-RPC 2.0 A2A response: {jsonrpc, id, result: Message|Task}
    result = payload.get("result")
    if isinstance(result, dict):
        kind = result.get("kind")
        if kind == "message":
            text = _text_from_parts(result.get("parts") or [])
            if text:
                return text
        elif kind == "task":
            for artifact in result.get("artifacts") or []:
                text = _text_from_parts(artifact.get("parts") or [])
                if text:
                    return text
            status_msg = (result.get("status") or {}).get("message") or {}
            text = _text_from_parts(status_msg.get("parts") or [])
            if text:
                return text

    # Legacy / fallback formats
    for key in ("output", "message", "content", "text"):
        if key in payload and isinstance(payload[key], str):
            return payload[key]
        if key in payload and isinstance(payload[key], dict):
            inner = payload[key]
            if "text" in inner:
                return inner.get("text")
            if "parts" in inner:
                text = _text_from_parts(inner.get("parts") or [])
                if text:
                    return text
    events = payload.get("events") or payload.get("outputs") or []
    for ev in events:
        content = ev.get("content") or {}
        text = _text_from_parts(content.get("parts") or [])
        if text:
            return text
    return ""


def _extract_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def _parse_quote(resp: dict) -> QuoteResponse | None:
    text = _extract_text(resp)
    if not text:
        logger.warning("_parse_quote no_text raw=%s", json.dumps(resp)[:500])
        return None
    data = _extract_json(text)
    if not data:
        logger.warning("_parse_quote failed text=%s", text[:300])
        return None
    if data.get("type") != "quote":
        logger.warning("_parse_quote wrong_type type=%s text=%s", data.get("type"), text[:300])
        return None
    try:
        return QuoteResponse(**data)
    except Exception as exc:
        logger.warning("_parse_quote schema_error exc=%s data=%s", exc, str(data)[:300])
        return None


def _parse_negotiation_response(resp: dict) -> dict | None:
    text = _extract_text(resp)
    if not text:
        return None
    data = _extract_json(text)
    if not data or data.get("type") != "negotiation_response":
        return None
    return data


async def broadcast_rfq(suppliers: List[Supplier], bom: BOM, negotiation_id: str) -> List[QuoteResponse]:
    tasks = []
    buyer_id = "buyer-nexus"
    logger.info("broadcast_rfq start negotiation_id=%s suppliers=%s", negotiation_id, [s.id for s in suppliers])
    for s in suppliers:
        rfq = RFQMessage(
            type="rfq",
            negotiation_id=negotiation_id,
            buyer_id=buyer_id,
            supplier_id=s.id,
            items=bom.items,
            destination_region=bom.destination_region,
            deadline_days=bom.deadline_days,
            required_certifications=[],
        )
        tasks.append(send_a2a_message(rfq.model_dump()))

    responses = await asyncio.gather(*tasks, return_exceptions=True)
    quotes: List[QuoteResponse] = []
    for idx, resp in enumerate(responses):
        supplier_id = suppliers[idx].id if idx < len(suppliers) else None
        if isinstance(resp, Exception):
            logger.warning("broadcast_rfq supplier_error supplier_id=%s error=%s", supplier_id, repr(resp))
            continue
        quote = _parse_quote(resp)
        if quote:
            quotes.append(quote)
        else:
            logger.warning("broadcast_rfq unparseable_quote supplier_id=%s", supplier_id)
    logger.info("broadcast_rfq done quotes=%d total_suppliers=%d", len(quotes), len(suppliers))
    return quotes


def score_quote(quote: QuoteResponse, bom: BOM) -> float:
    budget_per_unit = _get_budget_per_unit(bom)
    price_score = (
        1.0 - min(quote.unit_price / budget_per_unit, 1.0)
        if budget_per_unit
        else 0.5
    )
    lead_score = 1.0 - min(quote.lead_time_days / max(bom.deadline_days, 1), 1.0)
    with get_db_session() as db:
        supplier = db.query(Supplier).filter(Supplier.id == quote.supplier_id).first()
        trust = float(supplier.trust_score) if supplier else 0.5
        region_score = 1.0 if supplier and supplier.region == bom.destination_region else 0.5
    return (0.30 * price_score) + (0.25 * lead_score) + (0.25 * trust) + (0.20 * region_score)


def select_winner(quotes: List[QuoteResponse], bom: BOM) -> tuple[QuoteResponse, bool]:
    if not quotes:
        raise HTTPException(status_code=404, detail="No supplier quotes received.")
    if random.random() < EPSILON:
        return random.choice(quotes), True
    return max(quotes, key=lambda q: score_quote(q, bom)), False


def compute_negotiation_params(winner: QuoteResponse, bom: BOM) -> dict:
    supplier_price = winner.unit_price
    discount = choose_discount(winner.supplier_id)
    open_offer = round(supplier_price * (1 - discount), 2)
    if bom.budget:
        budget_per_unit = bom.budget / bom.items[0].quantity
        counter_offer = round(budget_per_unit * 0.95, 2)
        walkaway = round(budget_per_unit * 1.00, 2)
    else:
        counter_offer = round(supplier_price * 0.92, 2)
        walkaway = round(supplier_price * 1.00, 2)
    return {
        "open_offer": open_offer,
        "counter_offer": counter_offer,
        "walkaway_price": walkaway,
        "supplier_ask": supplier_price,
    }


def _save_message(negotiation_id: str, round_no: int, sender: str, msg_type: str, message: str, price: float | None, payload: dict | None = None) -> None:
    with get_db_session() as db:
        db.add(
            Message(
                negotiation_id=negotiation_id,
                round=round_no,
                sender=sender,
                message_type=msg_type,
                human_message=message,
                price=price,
                payload=json.dumps(payload or {}),
            )
        )
        db.commit()


def _update_negotiation(negotiation_id: str, **kwargs) -> None:
    with get_db_session() as db:
        neg = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
        if not neg:
            return
        for k, v in kwargs.items():
            setattr(neg, k, v)
        db.commit()


def _finalize_negotiation(negotiation_id: str, outcome: str, buyer_budget: float | None) -> None:
    with get_db_session() as db:
        neg = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
        if not neg:
            return
        supplier = db.query(Supplier).filter(Supplier.id == neg.supplier_id).first()
        if not supplier:
            return
        initial_ask = float(neg.initial_supplier_ask or 0.0)
        final_price = float(neg.final_price or 0.0)
        discount_given = max(initial_ask - final_price, 0.0)
        total_deals = supplier.total_deals or 0
        successful = supplier.successful_deals or 0
        reward = compute_reward(outcome, discount_given, neg.current_round, neg.max_rounds)
        updated = update_scores(supplier.trust_score or 0.75, total_deals, successful, reward, outcome)
        supplier.trust_score = updated.new_trust
        supplier.fit_score = updated.new_fit
        supplier.total_deals = total_deals + 1
        supplier.successful_deals = successful + (1 if outcome == "accepted" else 0)
        discount_asked = 1.0 - (float(neg.open_offer) / float(neg.initial_supplier_ask)) if neg.initial_supplier_ask else 0.15
        discount_achieved = max(initial_ask - final_price, 0.0) / initial_ask if initial_ask else 0.0
        db.add(
            Message(
                negotiation_id=negotiation_id,
                round=neg.current_round,
                sender="system",
                message_type="rl_update",
                human_message=f"RL update reward={updated.reward}",
                price=None,
                payload=json.dumps({"reward": updated.reward, "new_trust": updated.new_trust, "new_fit": updated.new_fit}),
            )
        )
        db.commit()
        record_outcome(supplier.id, discount_asked, discount_achieved)


def _accepted_result(neg: Negotiation, supplier_name: str, lead_time_days: int, rounds: int) -> ProcurementResult:
    contract_id = f"CONTRACT-{neg.id[:8].upper()}"
    return ProcurementResult(
        success=True,
        negotiation_id=neg.id,
        supplier_id=neg.supplier_id,
        supplier_name=supplier_name,
        final_price=neg.final_price,
        total_cost=round(neg.final_price * neg.quantity, 2),
        lead_time_days=lead_time_days,
        rounds_taken=rounds,
        contract_id=contract_id,
        all_initial_quotes=[],
    )


async def negotiate(negotiation_id: str, winner: QuoteResponse, params: dict, bom: BOM) -> ProcurementResult:
    current_price = params["supplier_ask"]
    logger.info(
        "negotiate start negotiation_id=%s supplier_id=%s supplier_name=%s supplier_ask=%s",
        negotiation_id,
        winner.supplier_id,
        winner.supplier_name,
        current_price,
    )
    if current_price <= params["open_offer"]:
        logger.info("negotiate immediate_accept negotiation_id=%s price=%s", negotiation_id, current_price)
        _save_message(
            negotiation_id,
            0,
            "system",
            "accepted",
            "Supplier quote already within open offer — accepted without negotiation",
            current_price,
        )
        _update_negotiation(
            negotiation_id,
            status="accepted",
            final_price=current_price,
            current_round=0,
        )
        generate_contract(negotiation_id)
        _finalize_negotiation(negotiation_id, "accepted", bom.budget)
        return _accepted_result(_load_negotiation(negotiation_id), winner.supplier_name, winner.lead_time_days, 0)

    for current_round in range(1, MAX_ROUNDS + 1):
        if current_round == 1:
            buyer_offer = params["open_offer"]
        elif current_round == 2:
            buyer_offer = params["counter_offer"]
        else:
            buyer_offer = params["walkaway_price"]

        message_text = f"We are offering €{buyer_offer}/unit for {bom.items[0].quantity}x {bom.product}. Please confirm."

        logger.info(
            "negotiate round=%d negotiation_id=%s buyer_offer=%s",
            current_round,
            negotiation_id,
            buyer_offer,
        )
        _save_message(negotiation_id, current_round, "buyer", "counter_offer", message_text, buyer_offer)

        counter = CounterOfferMessage(
            type="counter_offer",
            negotiation_id=negotiation_id,
            buyer_price=buyer_offer,
            round=current_round,
            message=message_text,
        )
        response_raw = await send_a2a_message(counter.model_dump())
        response = _parse_negotiation_response(response_raw)
        if not response:
            logger.warning(
                "negotiate response_unreadable negotiation_id=%s round=%d raw_text=%s",
                negotiation_id,
                current_round,
                _extract_text(response_raw)[:500],
            )
            return await build_failure_result(negotiation_id, "Supplier response unreadable", current_price, bom, params)

        _save_message(
            negotiation_id,
            current_round,
            "supplier",
            "negotiation_response",
            response.get("rationale") or "",
            response.get("counter_price") or buyer_offer,
            response,
        )

        logger.info(
            "negotiate response negotiation_id=%s round=%d accepted=%s counter_price=%s",
            negotiation_id,
            current_round,
            response.get("accepted"),
            response.get("counter_price"),
        )

        if response.get("accepted"):
            final_price = buyer_offer
            _update_negotiation(
                negotiation_id,
                status="accepted",
                final_price=final_price,
                current_round=current_round,
            )
            generate_contract(negotiation_id)
            _finalize_negotiation(negotiation_id, "accepted", bom.budget)
            return _accepted_result(_load_negotiation(negotiation_id), winner.supplier_name, winner.lead_time_days, current_round)

        counter_price = response.get("counter_price")
        if counter_price is None:
            return await build_failure_result(negotiation_id, "Supplier rejected without counter", current_price, bom, params)

        if counter_price <= params["walkaway_price"]:
            _update_negotiation(
                negotiation_id,
                status="accepted",
                final_price=counter_price,
                current_round=current_round,
            )
            generate_contract(negotiation_id)
            _finalize_negotiation(negotiation_id, "accepted", bom.budget)
            return _accepted_result(_load_negotiation(negotiation_id), winner.supplier_name, winner.lead_time_days, current_round)

        if current_round == MAX_ROUNDS:
            return await build_failure_result(negotiation_id, "Supplier could not meet budget after 3 rounds", counter_price, bom, params)

        current_price = counter_price

    return await build_failure_result(negotiation_id, "Negotiation failed", current_price, bom, params)


def _load_negotiation(negotiation_id: str) -> Negotiation:
    with get_db_session() as db:
        return db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()


def _quotes_from_snapshot(snapshot: str) -> List[QuoteResponse]:
    try:
        data = json.loads(snapshot or "[]")
        return [QuoteResponse(**q) for q in data]
    except Exception:
        return []


async def build_failure_result(negotiation_id: str, reason: str, supplier_best_price: float, bom: BOM, params: dict) -> ProcurementResult:
    logger.warning(
        "build_failure_result negotiation_id=%s reason=%s supplier_best_price=%s",
        negotiation_id,
        reason,
        supplier_best_price,
    )
    neg = _load_negotiation(negotiation_id)
    all_quotes = _quotes_from_snapshot(neg.shortlist_snapshot or "[]") if neg else []
    remaining = [q for q in all_quotes if q.supplier_id != (neg.supplier_id if neg else "")]

    other_options = []
    for idx, quote in enumerate(remaining, start=1):
        within_budget = params["walkaway_price"] is not None and quote.unit_price <= params["walkaway_price"]
        other_options.append(
            {
                "supplier": quote.supplier_name,
                "supplier_id": quote.supplier_id,
                "quoted_price": quote.unit_price,
                "total": quote.total_price,
                "lead_time_days": quote.lead_time_days,
                "rank": idx,
                "note": f"Quoted €{quote.unit_price}/unit — {'within budget' if within_budget else 'above budget but negotiable'}",
            }
        )

    suggestion = None
    if remaining:
        cheapest = min(remaining, key=lambda q: q.unit_price)
        gap = supplier_best_price - params["walkaway_price"]
        suggestion = (
            f"{cheapest.supplier_name} quoted €{cheapest.unit_price}/unit"
            + (" which is within your budget." if cheapest.unit_price <= params["walkaway_price"] else f" — increasing budget by €{gap * bom.items[0].quantity:.0f} would close this deal.")
        )

    _update_negotiation(negotiation_id, status="failed")
    _finalize_negotiation(negotiation_id, "failed", bom.budget)

    return ProcurementResult(
        success=False,
        negotiation_id=negotiation_id,
        failure_reason=reason,
        closest_offer={
            "supplier": neg.supplier_id if neg else None,
            "their_best_price": supplier_best_price,
            "your_walkaway": params["walkaway_price"],
            "gap_per_unit": round(supplier_best_price - params["walkaway_price"], 2),
        },
        other_options=other_options,
        suggestion=suggestion,
        all_initial_quotes=all_quotes,
    )


def create_negotiation_record(bom: BOM, shortlist_snapshot: List[QuoteResponse], supplier_id: str | None = None, explored: bool = False, parent_negotiation_id: str | None = None) -> str:
    neg_id = f"neg-{uuid.uuid4().hex[:8]}"
    with get_db_session() as db:
        neg = Negotiation(
            id=neg_id,
            supplier_id=supplier_id,
            buyer_id="buyer-nexus",
            status="active",
            current_round=0,
            max_rounds=MAX_ROUNDS,
            product=bom.product,
            product_category=bom.items[0].category if bom.items else "other",
            quantity=bom.items[0].quantity if bom.items else 1,
            destination_region=bom.destination_region,
            bom_snapshot=bom.model_dump_json(),
            shortlist_snapshot=json.dumps([q.model_dump() for q in shortlist_snapshot]),
            explored=explored,
            expires_at=create_expiry(24),
            parent_negotiation_id=parent_negotiation_id,
        )
        db.add(neg)
        db.commit()
    return neg_id


async def run_procurement(req: ProcurementRequest) -> ProcurementResult:
    bom = await parse_procurement_request(req)
    suppliers = discover_suppliers(bom)
    negotiation_id = create_negotiation_record(bom, [], None)
    logger.info(
        "run_procurement start negotiation_id=%s product=%s quantity=%s suppliers=%d",
        negotiation_id,
        bom.product,
        bom.items[0].quantity if bom.items else None,
        len(suppliers),
    )
    quotes = await broadcast_rfq(suppliers, bom, negotiation_id)

    if not quotes:
        logger.warning("run_procurement no_quotes negotiation_id=%s", negotiation_id)
        _update_negotiation(negotiation_id, status="failed")
        return ProcurementResult(
            success=False,
            negotiation_id=negotiation_id,
            failure_reason="No suppliers responded in time",
            other_options=[],
            all_initial_quotes=[],
        )

    winner, explored = select_winner(quotes, bom)
    params = compute_negotiation_params(winner, bom)

    _update_negotiation(
        negotiation_id,
        supplier_id=winner.supplier_id,
        open_offer=params["open_offer"],
        counter_offer=params["counter_offer"],
        walkaway_price=params["walkaway_price"],
        current_price=params["supplier_ask"],
        initial_supplier_ask=params["supplier_ask"],
        explored=explored,
        shortlist_snapshot=json.dumps([q.model_dump() for q in quotes]),
    )

    return await negotiate(negotiation_id, winner, params, bom)


async def retry_procurement(retry_req) -> ProcurementResult:
    logger.info("retry_procurement start negotiation_id=%s", retry_req.negotiation_id)
    with get_db_session() as db:
        original = db.query(Negotiation).filter(Negotiation.id == retry_req.negotiation_id).first()
        if not original:
            raise HTTPException(status_code=404, detail="Original negotiation not found")

    bom = BOM.model_validate_json(original.bom_snapshot)
    if retry_req.updated_budget is not None:
        bom.budget = retry_req.updated_budget
    if retry_req.updated_deadline_days is not None:
        bom.deadline_days = retry_req.updated_deadline_days

    all_quotes = _quotes_from_snapshot(original.shortlist_snapshot or "[]")
    chosen = next((q for q in all_quotes if q.supplier_id == retry_req.supplier_id), None)
    if not chosen:
        raise HTTPException(status_code=404, detail="Supplier quote not found in shortlist")

    new_negotiation_id = create_negotiation_record(bom, all_quotes, retry_req.supplier_id, False, original.id)
    params = compute_negotiation_params(chosen, bom)

    _update_negotiation(
        new_negotiation_id,
        supplier_id=chosen.supplier_id,
        open_offer=params["open_offer"],
        counter_offer=params["counter_offer"],
        walkaway_price=params["walkaway_price"],
        current_price=params["supplier_ask"],
        initial_supplier_ask=params["supplier_ask"],
    )

    return await negotiate(new_negotiation_id, chosen, params, bom)


async def run_procurement_tool(
    request: str,
    destination_region: str | None = None,
    budget: float | None = None,
    deadline_days: int | None = 7,
) -> dict:
    def _coerce(val, typ):
        if val is None or str(val).strip().lower() in ("none", "null", ""):
            return None
        try:
            return typ(val)
        except Exception:
            return None
    result = await run_procurement(
        ProcurementRequest(
            request=request,
            destination_region=_coerce(destination_region, str),
            budget=_coerce(budget, float),
            deadline_days=_coerce(deadline_days, int) or 7,
        )
    )
    return result.model_dump()
