import os
import uvicorn
import json
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.adk.cli.fast_api import get_fast_api_app
from logger import setup_logger
from db import ADK_DATABASE_URL
from request_middleware import attach_request_middleware

# Load environment variables
load_dotenv()
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

log = setup_logger("intent_parser.server")

# Import supplier agent components
from supplier.QuoteAgent.agent import get_supplier_agent
from supplier.supplier_registry import SupplierRegistry
from supplier.supplier_catalog import seed_suppliers


# ============================================================================
# PYDANTIC MODELS FOR API
# ============================================================================

class RFQItem(BaseModel):
    """Individual line item in an RFQ"""
    product_id: str
    quantity: int


class RFQRequest(BaseModel):
    """Request for Quote from a buyer to a supplier"""
    buyer_id: str
    items: List[RFQItem]
    delivery_region: str
    deadline_days: int
    max_budget: Optional[float] = None
    required_certifications: List[str] = []
    negotiation_style: Optional[str] = "balanced"


class SupplierRegistrationRequest(BaseModel):
    """Supplier registration request"""
    supplier_id: str
    company_name: str
    country: str
    region: str
    certifications: List[str]
    contact_email: str
    trust_score: Optional[float] = 0.5
    negotiation_style: Optional[str] = "balanced"


class SupplierDiscoveryRequest(BaseModel):
    """Request to discover suppliers"""
    capability: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    min_trust_score: Optional[float] = 0.5
    certifications_required: List[str] = []


# ============================================================================
# GET FAST API APP WITH BUYER AGENTS
# ============================================================================

buyer_app = get_fast_api_app(
    agents_dir="buyer_agents",
    session_service_uri=ADK_DATABASE_URL,
    web=True,
    a2a=True,
    host="0.0.0.0",
    port=8010,
)

# ============================================================================
# CREATE MAIN APP WITH SUPPLIER ENDPOINTS
# ============================================================================

app = FastAPI(
    title="NEXUS Supply Chain Platform",
    description="AI-powered procurement with buyer and supplier agents",
    version="1.0.0"
)

# Attach middleware to the main app
attach_request_middleware(app, log, llm_delay_seconds=10)

# Mount buyer agents
app.mount("/buyer", buyer_app)


# ============================================================================
# SUPPLIER AGENT ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize supplier registry on startup"""
    print("\n=== NEXUS Supply Chain Platform Starting ===\n")
    
    # Seed sample suppliers (only if database is empty)
    try:
        existing_suppliers = SupplierRegistry.list_all_suppliers(limit=1)
        if not existing_suppliers:
            print("Initializing supplier catalog...")
            
            # Check if suppliers.json exists
            suppliers_json_path = Path("supplier/suppliers.json")
            if suppliers_json_path.exists():
                print("Found suppliers.json - importing suppliers...")
                try:
                    from supplier.import_suppliers import import_suppliers
                    result = import_suppliers("supplier/suppliers.json", verbose=False)
                    if result.get("success"):
                        print(f"✓ Imported {result['suppliers_registered']} suppliers, {result['products_added']} products")
                    else:
                        print(f"Note: Import from JSON failed, using default catalog...")
                        seed_suppliers()
                except Exception as e:
                    print(f"Note: Could not import from JSON ({e}), using default catalog...")
                    seed_suppliers()
            else:
                # No JSON file, use default seeding
                seed_suppliers()
        else:
            print(f"Supplier catalog already initialized with {len(existing_suppliers)} suppliers")
    except Exception as e:
        print(f"Note: Supplier catalog seeding skipped: {str(e)}")
    
    print("\n=== Platform Ready ===\n")


@app.post("/api/rfq")
async def handle_rfq(rfq: RFQRequest):
    """
    Handle an RFQ (Request for Quote) from a buyer.
    Routes to the appropriate supplier agent based on products requested.
    """
    try:
        if not rfq.items:
            raise HTTPException(status_code=400, detail="No items requested")
        
        # Extract product categories from requested items
        categories = set()
        for item in rfq.items:
            categories.add("temperature_sensors")  # Demo default
        
        # Discover suppliers that match requirements
        suppliers = SupplierRegistry.discover_suppliers(
            capability=list(categories)[0] if categories else None,
            region=rfq.delivery_region,
            min_trust_score=0.7,
            certifications_required=rfq.required_certifications,
            limit=5
        )
        
        if not suppliers:
            raise HTTPException(
                status_code=404,
                detail=f"No suppliers found matching your requirements in {rfq.delivery_region}"
            )
        
        # Create RFQ payload for supplier agents
        items_list = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity
            }
            for item in rfq.items
        ]
        
        quotes = []
        
        # Query each supplier agent for quotes
        for supplier in suppliers[:3]:  # Query top 3 suppliers
            try:
                supplier_id = supplier["supplier_id"]
                
                # Get or create supplier agent
                agent = get_supplier_agent(supplier_id)
                
                # Build RFQ message for the agent
                rfq_message = {
                    "buyer_id": rfq.buyer_id,
                    "items": items_list,
                    "delivery_region": rfq.delivery_region,
                    "deadline_days": rfq.deadline_days,
                    "required_certifications": rfq.required_certifications,
                    "negotiation_style": rfq.negotiation_style
                }
                
                # Invoke the supplier agent
                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": json.dumps(rfq_message)}]}
                )
                
                if result and "quote" in str(result):
                    quotes.append({
                        "supplier_id": supplier_id,
                        "supplier_name": supplier["company_name"],
                        "supplier_trust_score": supplier["trust_score"],
                        "quote": result
                    })
                    
            except Exception as e:
                print(f"Error getting quote from supplier {supplier['supplier_id']}: {e}")
                continue
        
        if not quotes:
            # Return supplier options even if quotes weren't generated
            quotes = [
                {
                    "supplier_id": s["supplier_id"],
                    "supplier_name": s["company_name"],
                    "supplier_trust_score": s["trust_score"],
                    "status": "quote_pending"
                }
                for s in suppliers[:3]
            ]
        
        return {
            "rfq_id": rfq.buyer_id,
            "status": "quotes_received",
            "requested_items": len(rfq.items),
            "suppliers_contacted": len(suppliers),
            "quotes_received": len(quotes),
            "quotes": quotes,
            "next_action": "negotiation_agent" if quotes else "supplier_discovery"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suppliers")
async def list_suppliers(
    region: Optional[str] = None,
    country: Optional[str] = None,
    capability: Optional[str] = None,
    limit: int = 20
):
    """List available suppliers in the registry."""
    try:
        suppliers = SupplierRegistry.discover_suppliers(
            capability=capability,
            region=region,
            country=country,
            limit=limit
        )
        
        return {
            "suppliers_found": len(suppliers),
            "suppliers": suppliers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str):
    """Get detailed information about a specific supplier"""
    try:
        supplier = SupplierRegistry.get_supplier_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suppliers/register")
async def register_supplier(req: SupplierRegistrationRequest):
    """Register a new supplier in the NEXUS network."""
    try:
        result = SupplierRegistry.register_supplier(
            supplier_id=req.supplier_id,
            company_name=req.company_name,
            country=req.country,
            region=req.region,
            certifications=req.certifications,
            capabilities=[],
            contact_email=req.contact_email,
            trust_score=req.trust_score,
            negotiation_style=req.negotiation_style
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suppliers/{supplier_id}/quote")
async def get_supplier_quote(supplier_id: str, rfq: RFQRequest):
    """Get a quote directly from a specific supplier."""
    try:
        agent = get_supplier_agent(supplier_id)
        items_list = [{"product_id": item.product_id, "quantity": item.quantity} for item in rfq.items]
        
        rfq_message = {
            "buyer_id": rfq.buyer_id,
            "items": items_list,
            "delivery_region": rfq.delivery_region,
            "deadline_days": rfq.deadline_days,
            "required_certifications": rfq.required_certifications,
            "negotiation_style": rfq.negotiation_style
        }
        
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": json.dumps(rfq_message)}]}
        )
        
        return {
            "supplier_id": supplier_id,
            "rfq_request": rfq_message,
            "quote_response": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "NEXUS Supply Chain",
        "version": "1.0.0"
    }


@app.get("/api/info")
async def platform_info():
    """Get platform information"""
    return {
        "platform": "NEXUS Supply Chain Intelligence Platform",
        "description": "AI-powered procurement with buyer and supplier agents",
        "endpoints": {
            "buyer_agents": "/buyer",
            "rfq": "/api/rfq",
            "suppliers": "/api/suppliers",
            "supplier_registration": "/api/suppliers/register",
            "supplier_quote": "/api/suppliers/{supplier_id}/quote"
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)
