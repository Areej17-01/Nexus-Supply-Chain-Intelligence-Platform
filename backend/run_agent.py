import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

from google.adk.cli.fast_api import get_fast_api_app

from nexus.core.db import ADK_DATABASE_URL
from nexus.core.logger import setup_logger
from nexus.core.middleware import attach_request_middleware



def main():
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    load_dotenv(project_root / ".env")

    role = (os.getenv("AGENT_ROLE") or "buyer").lower().strip()

    # Key selection: ADK's Gemini client reads API key from env.
    # To truly split usage, run buyer and supplier as separate processes with different envs.
    if role == "supplier":
        if not os.getenv("GOOGLE_API_KEY") and os.getenv("SUPPLIER_GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("SUPPLIER_GEMINI_API_KEY", "")
        elif not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    else:
        if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

    log = setup_logger("procurement.run_agent")
    app_name = os.getenv("APP_NAME", "ProcurementOrchestrator")
    port = int(os.getenv("PORT", "8010"))
    host = os.getenv("HOST", "0.0.0.0")

    if role == "supplier":
        valid_apps = {"QuoteAgent"}
        agents_dir = backend_dir / "supplier"
    else:
        valid_apps = {"IntentParser", "ProcurementOrchestrator"}
        agents_dir = backend_dir / "buyer_agents"

    if app_name not in valid_apps:
        valid = ", ".join(sorted(valid_apps))
        raise ValueError(f"Unknown APP_NAME '{app_name}'. Valid values: {valid}")

    enable_a2a = os.getenv("ENABLE_A2A", "false").lower() == "true"
    app = get_fast_api_app(
        agents_dir=str(agents_dir),
        session_service_uri=ADK_DATABASE_URL,
        web=True,
        a2a=enable_a2a,
        host=host,
        port=port,
    )



    try:
        llm_delay_seconds = float(os.getenv("LLM_DELAY_SECONDS", "6"))
    except Exception:
        llm_delay_seconds = 6.0
    attach_request_middleware(app, log, llm_delay_seconds=llm_delay_seconds)

    print(f"Serving ADK apps on {host}:{port}. Use app_name='{app_name}' in /run payload.")
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()

