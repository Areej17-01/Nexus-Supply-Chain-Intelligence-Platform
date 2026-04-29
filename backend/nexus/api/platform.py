from typing import Optional
from fastapi import APIRouter, HTTPException
from nexus.core.logger import setup_logger
from nexus.core.middleware import get_llm_metrics_snapshot
from supplier.supplier_registry import SupplierRegistry
from agents.orchestrator import ProcurementOrchestrator

router = APIRouter()
log = setup_logger("nexus.api.platform")
orchestrator = ProcurementOrchestrator()


@router.get("/suppliers")
async def list_suppliers(
    region: Optional[str] = None,
    country: Optional[str] = None,
    capability: Optional[str] = None,
    limit: int = 20
):
    try:
        suppliers = SupplierRegistry.discover_suppliers(
            capability=capability,
            region=region,
            country=country,
            limit=limit
        )
        return {"suppliers_found": len(suppliers), "suppliers": suppliers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry")
async def list_agent_registry(role: Optional[str] = None, region: Optional[str] = None, capability: Optional[str] = None):
    agents = orchestrator.registry.list_agents(role=role, region=region, capability=capability, min_trust=0.0)
    return {"agents_found": len(agents), "agents": agents}


@router.get("/llm/metrics")
async def llm_metrics():
    return get_llm_metrics_snapshot()


# --- DEAD ENDPOINTS (not called by UI, kept for reference) ---
# @router.get("/health")
# @router.get("/info")
# @router.post("/procure")             — replaced by POST /buyer/run_sse (ADK)
# @router.api_route("/procure/stream") — replaced by POST /buyer/run_sse (ADK)
# @router.post("/negotiate")           — replaced by ADK negotiation_agent tool
# @router.post("/contract/generate")   — replaced by ADK contract_agent tool
# @router.post("/rfq")                 — replaced by ADK send_rfq_to_supplier tool
