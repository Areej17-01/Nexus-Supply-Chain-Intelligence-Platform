import asyncio
import json
import logging
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app

from nexus.buyer.negotiation import run_procurement, retry_procurement
from nexus.config import ADK_DATABASE_URL, DEBUG, HOST, PLATFORM_NAME, PORT, VERSION
from nexus.database import Contract, Message, Negotiation, Supplier, cleanup_expired_negotiations, get_db_session, init_db
from nexus.protocols.schemas import ProcurementRequest, ProcurementResult, RetryRequest, SupplierUpsert
from nexus.scripts.seed_suppliers import seed_suppliers

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
FRONTEND_CANDIDATES = [
    PROJECT_ROOT / "frontend new" / "static",
    PROJECT_ROOT / "frontend" / "static",
    Path.cwd() / "frontend new" / "static",
    Path.cwd() / "frontend" / "static",
]
FRONTEND_STATIC_DIR = next((p for p in FRONTEND_CANDIDATES if p.exists()), FRONTEND_CANDIDATES[0])
BUYER_AGENTS_DIR = BASE_DIR / "buyer"
SUPPLIER_AGENTS_DIR = BASE_DIR / "supplier"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "procurement.log"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_level = logging.DEBUG if DEBUG else logging.INFO
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


setup_logging()

import litellm  # noqa: E402
litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.WARNING)

app = FastAPI(title=PLATFORM_NAME, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

buyer_app = get_fast_api_app(
    agents_dir=str(BUYER_AGENTS_DIR),
    session_service_uri=ADK_DATABASE_URL,
    web=True,
    a2a=True,
    auto_create_session=True,
)

supplier_app = get_fast_api_app(
    agents_dir=str(SUPPLIER_AGENTS_DIR),
    session_service_uri=ADK_DATABASE_URL,
    web=True,
    a2a=True,
    auto_create_session=True,
)

app.mount("/buyer", buyer_app)
app.mount("/supplier", supplier_app)

if FRONTEND_STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_STATIC_DIR)), name="static")


@app.get("/")
def read_index():
    index_path = FRONTEND_STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return PlainTextResponse(f"Frontend not found at {index_path}", status_code=404)


@app.post("/procure", response_model=ProcurementResult)
async def procure(req: ProcurementRequest):
    return await run_procurement(req)


@app.post("/procure/retry", response_model=ProcurementResult)
async def procure_retry(req: RetryRequest):
    return await retry_procurement(req)


@app.post("/suppliers")
def upsert_supplier(payload: SupplierUpsert):
    def _normalize_list(value):
        if not value:
            return []
        if isinstance(value, list):
            return [v for v in value if v]
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return [v.strip() for v in str(value).split(',') if v.strip()]

    def _normalize_map(value):
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _to_float(value, fallback):
        try:
            n = float(value)
            return n if n > 0 else fallback
        except Exception:
            return fallback

    def _to_discount(value, fallback):
        try:
            n = float(value)
            if n < 0:
                return 0.0
            if n > 95:
                return 95.0
            return n
        except Exception:
            return fallback

    caps = _normalize_list(payload.capabilities)
    certs = _normalize_list(payload.certifications)
    supplier_id = payload.supplier_id.strip()
    company_name = (payload.company_name or supplier_id).strip()
    country = (payload.country or "Unknown").strip()
    region = (payload.region or "Global").strip()
    trust_score = payload.trust_score if payload.trust_score is not None else 0.75
    lead_time_days = payload.lead_time_days if payload.lead_time_days is not None else 14

    input_base_map = _normalize_map(payload.base_price_map)
    input_discount_map = _normalize_map(payload.discount_percent_map)

    if not caps and input_base_map:
        caps = [k for k in input_base_map.keys() if k and k != "default"]

    base_price_map = {}
    price_floor_map = {}
    for cap in caps:
        base_price = round(_to_float(input_base_map.get(cap, input_base_map.get("default", 5.0)), 5.0), 2)
        discount_pct = _to_discount(input_discount_map.get(cap, input_discount_map.get("default", 10.0)), 10.0)
        floor_price = round(max(base_price * (1 - (discount_pct / 100.0)), 0.01), 2)
        base_price_map[cap] = base_price
        price_floor_map[cap] = floor_price

    default_base = round(_to_float(input_base_map.get("default", 5.0), 5.0), 2)
    default_discount = _to_discount(input_discount_map.get("default", 10.0), 10.0)
    base_price_map["default"] = default_base
    price_floor_map["default"] = round(max(default_base * (1 - (default_discount / 100.0)), 0.01), 2)

    with get_db_session() as db:
        existing = db.query(Supplier).filter(Supplier.id == supplier_id).first()

        if existing:
            existing.name = company_name
            existing.country = country
            existing.region = region
            existing.categories = json.dumps(caps)
            existing.capabilities = json.dumps(caps)
            existing.certifications = json.dumps(certs)
            existing.trust_score = trust_score
            existing.lead_time_days = lead_time_days
            existing.base_price_map = json.dumps(base_price_map)
            existing.price_floor_map = json.dumps(price_floor_map)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            supplier = existing
        else:
            supplier = Supplier(
                id=supplier_id,
                name=company_name,
                country=country,
                region=region,
                categories=json.dumps(caps),
                capabilities=json.dumps(caps),
                base_price_map=json.dumps(base_price_map),
                price_floor_map=json.dumps(price_floor_map),
                lead_time_days=lead_time_days,
                certifications=json.dumps(certs),
                trust_score=trust_score,
                fit_score=0.50,
            )
            db.add(supplier)
            db.commit()
            db.refresh(supplier)

    return {
        "id": supplier.id,
        "name": supplier.name,
        "region": supplier.region,
        "country": supplier.country,
        "capabilities": caps,
        "certifications": certs,
        "trust_score": supplier.trust_score,
        "fit_score": supplier.fit_score,
        "lead_time_days": supplier.lead_time_days,
        "base_price_map": base_price_map,
        "price_floor_map": price_floor_map,
        "total_deals": supplier.total_deals,
        "successful_deals": supplier.successful_deals,
    }


@app.get("/suppliers")
def list_suppliers():
    def _parse_list(value):
        if isinstance(value, list):
            return value
        if not value:
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return [v.strip() for v in str(value).split(',') if v.strip()]

    def _parse_map(value):
        if isinstance(value, dict):
            return value
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    with get_db_session() as db:
        suppliers = db.query(Supplier).all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "region": s.region,
                "country": s.country,
                "capabilities": _parse_list(s.capabilities),
                "certifications": _parse_list(s.certifications),
                "trust_score": s.trust_score,
                "fit_score": s.fit_score,
                "lead_time_days": s.lead_time_days,
                "base_price_map": _parse_map(s.base_price_map),
                "price_floor_map": _parse_map(s.price_floor_map),
                "total_deals": s.total_deals,
                "successful_deals": s.successful_deals,
            }
            for s in suppliers
        ]


@app.get("/negotiations/{negotiation_id}")
def get_negotiation(negotiation_id: str):
    with get_db_session() as db:
        neg = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
        if not neg:
            return {"error": "Negotiation not found"}
        try:
            shortlist = json.loads(neg.shortlist_snapshot or "[]")
        except Exception:
            shortlist = []

        supplier_name = None
        if neg.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == neg.supplier_id).first()
            supplier_name = supplier.name if supplier else None

        return {
            "id": neg.id,
            "supplier_id": neg.supplier_id,
            "supplier_name": supplier_name,
            "buyer_id": neg.buyer_id,
            "status": neg.status,
            "current_round": neg.current_round,
            "open_offer": neg.open_offer,
            "counter_offer": neg.counter_offer,
            "walkaway_price": neg.walkaway_price,
            "final_price": neg.final_price,
            "product": neg.product,
            "quantity": neg.quantity,
            "destination_region": neg.destination_region,
            "explored": neg.explored,
            "shortlist": shortlist,
            "created_at": neg.created_at,
            "updated_at": neg.updated_at,
        }


@app.get("/negotiations/{negotiation_id}/transcript")
def get_transcript(negotiation_id: str):
    with get_db_session() as db:
        neg = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
        if not neg:
            return {"error": "Negotiation not found"}
        messages = db.query(Message).filter(Message.negotiation_id == negotiation_id).order_by(Message.id).all()
        start = neg.created_at or messages[0].timestamp if messages else neg.created_at
        end = messages[-1].timestamp if messages else neg.updated_at
        duration_seconds = int((end - start).total_seconds()) if start and end else 0

        transcript = [
            {
                "round": m.round,
                "sender": m.sender.upper(),
                "type": m.message_type,
                "timestamp": m.timestamp.isoformat() + "Z",
                "message": m.human_message,
                "price": m.price,
            }
            for m in messages
        ]
        summary = {
            "rounds_taken": neg.current_round,
            "buyer_open_offer": neg.open_offer,
            "buyer_walkaway": neg.walkaway_price,
            "supplier_initial_ask": neg.initial_supplier_ask,
            "supplier_best_offer": neg.final_price or neg.current_price,
            "outcome": neg.status,
        }
        return {
            "negotiation_id": negotiation_id,
            "supplier": neg.supplier_id,
            "product": f"{neg.product} x{neg.quantity}",
            "status": neg.status,
            "duration_seconds": duration_seconds,
            "transcript": transcript,
            "summary": summary,
        }


@app.get("/contracts")
def list_contracts():
    with get_db_session() as db:
        contracts = db.query(Contract).all()
        return [
            {
                "id": c.id,
                "negotiation_id": c.negotiation_id,
                "supplier_id": c.supplier_id,
                "total_value": c.total_value,
                "generated_at": c.generated_at,
            }
            for c in contracts
        ]


@app.get("/negotiations/{negotiation_id}/contract")
def get_contract(negotiation_id: str):
    with get_db_session() as db:
        contract = db.query(Contract).filter(Contract.negotiation_id == negotiation_id).first()
        if not contract:
            return {"error": "Contract not found"}
        return PlainTextResponse(contract.content, media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    init_db()
    seed_suppliers()
    cleanup_expired_negotiations()
    asyncio.create_task(_cleanup_loop())


async def _cleanup_loop():
    while True:
        cleanup_expired_negotiations()
        await asyncio.sleep(3600)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
