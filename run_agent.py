import os
import uvicorn
from dotenv import load_dotenv

from google.adk.cli.fast_api import get_fast_api_app

from db import ADK_DATABASE_URL
from logger import setup_logger
from request_middleware import attach_request_middleware


def main():
    load_dotenv("../.env")
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

    log = setup_logger("procurement.run_agent")
    app_name = os.getenv("APP_NAME", "ProcurementOrchestrator")
    port = int(os.getenv("PORT", "8010"))
    host = os.getenv("HOST", "0.0.0.0")
    valid_apps = {"IntentParser", "ProcurementOrchestrator"}
    if app_name not in valid_apps:
        valid = ", ".join(sorted(valid_apps))
        raise ValueError(f"Unknown APP_NAME '{app_name}'. Valid values: {valid}")

    app = get_fast_api_app(
        agents_dir="buyer_agents",
        session_service_uri=ADK_DATABASE_URL,
        web=True,
        a2a=True,
        host=host,
        port=port,
    )
    attach_request_middleware(app, log, llm_delay_seconds=10)
    print(f"Serving ADK apps on {host}:{port}. Use app_name='{app_name}' in /run payload.")
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()

