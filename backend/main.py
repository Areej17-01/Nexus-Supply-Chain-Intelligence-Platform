import os
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from google.adk.cli.fast_api import get_fast_api_app

from nexus.core.config import PLATFORM_NAME, VERSION, HOST, PORT, DEBUG, ENABLE_A2A
from nexus.core.db import ADK_DATABASE_URL
from nexus.core.logger import setup_logger
from nexus.core.middleware import attach_request_middleware
from nexus.api.platform import router as platform_router
from nexus.api.buyer import router as buyer_router
from nexus.api.supplier import router as supplier_router

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_STATIC_DIR = PROJECT_ROOT / "frontend" / "static"
BUYER_AGENTS_DIR = BACKEND_DIR / "buyer_agents"
SUPPLIER_AGENTS_DIR = BACKEND_DIR / "supplier"

# Setup Logging
log = setup_logger("nexus.server")

# Initialize App
app = FastAPI(
    title=PLATFORM_NAME,
    version=VERSION,
    description="Autonomous AI-powered procurement from intent to signed contract."
)

# Attach Middleware
try:
    LLM_DELAY_SECONDS = float(os.getenv("LLM_DELAY_SECONDS", "6"))
except Exception:
    LLM_DELAY_SECONDS = 6.0
attach_request_middleware(app, log, llm_delay_seconds=LLM_DELAY_SECONDS)

# Mount ADK Agents
# NEXUS Buyer Orchestrator
buyer_app = get_fast_api_app(
    agents_dir=str(BUYER_AGENTS_DIR),
    session_service_uri=ADK_DATABASE_URL,
    web=True,
    a2a=ENABLE_A2A,
    auto_create_session=True,
)
app.mount("/buyer", buyer_app)

# NEXUS Supplier Service
supplier_app = get_fast_api_app(
    agents_dir=str(SUPPLIER_AGENTS_DIR),
    session_service_uri=ADK_DATABASE_URL,
    web=True,
    a2a=ENABLE_A2A,
    auto_create_session=True,
)
app.mount("/supplier", supplier_app)

# Include API Routers
app.include_router(platform_router, prefix="/api", tags=["Platform"])
app.include_router(buyer_router, prefix="/api", tags=["Buyer"])
app.include_router(supplier_router, prefix="/api", tags=["Supplier"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("[UNHANDLED] %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Unhandled server error",
            "path": request.url.path,
            "error": str(exc),
        },
    )

# Serve Frontend
@app.get("/")
async def read_index():
    return FileResponse(str(FRONTEND_STATIC_DIR / "index.html"))

app.mount("/static", StaticFiles(directory=str(FRONTEND_STATIC_DIR)), name="static")

@app.on_event("startup")
async def startup():
    log.info("=== %s Starting ===", PLATFORM_NAME)
    try:
        from seed_nexus import seed_nexus_data
        seed_nexus_data()
        log.info("Database seeding checked/completed.")
    except Exception as e:
        log.warning("Seeding skipped or failed: %s", e)
    log.info("=== Platform Ready ===")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
