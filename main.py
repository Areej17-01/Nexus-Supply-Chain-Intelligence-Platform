import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

app = get_fast_api_app(
    agents_dir="buyer_agents",
    session_service_uri=None,
    web=True,
    a2a=False,
    host="0.0.0.0",
    port=8010,
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)