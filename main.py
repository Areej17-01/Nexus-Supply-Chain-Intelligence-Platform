import os
import uvicorn
from dotenv import load_dotenv
from google.adk.cli.fast_api import get_fast_api_app
from logger import setup_logger
from db import ADK_DATABASE_URL
from request_middleware import attach_request_middleware

load_dotenv("../.env")
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

log = setup_logger("intent_parser.server")

app = get_fast_api_app(
    agents_dir="buyer_agents",
    session_service_uri=ADK_DATABASE_URL,
    web=True,
    a2a=True,
    host="0.0.0.0",
    port=8010,
)

attach_request_middleware(app, log, llm_delay_seconds=10)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)