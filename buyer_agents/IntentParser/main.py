import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from buyer_agents.IntentParser.agent import root_agent


adk_app = get_fast_api_app(
    agent = root_agent,
    session_service_uri=None
)

app = FastAPI()
app.mount("/intent-parser",adk_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010, reload=True)