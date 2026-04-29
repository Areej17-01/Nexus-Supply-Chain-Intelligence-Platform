import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from nexus.buyer.negotiation import run_procurement_tool

# LiteLLM requires OPENROUTER_API_KEY but the project .env uses OPENROUTER_KEY
if not os.environ.get("OPENROUTER_API_KEY") and os.environ.get("OPENROUTER_KEY"):
    os.environ["OPENROUTER_API_KEY"] = os.environ["OPENROUTER_KEY"]

_raw_model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
MODEL = _raw_model if _raw_model.startswith("openrouter/") else f"openrouter/{_raw_model}"

model = LiteLlm(model=MODEL, api_key=os.environ.get("OPENROUTER_API_KEY", ""))

BUYER_AGENT_PROMPT = """
You are the Buyer Agent. The user message is a procurement request string.
Call run_procurement to execute the full procurement pipeline.
Return only the tool output.
""".strip()

root_agent = Agent(
    name="BuyerAgent",
    model=model,
    description="Parses buyer requests and orchestrates procurement.",
    instruction=BUYER_AGENT_PROMPT,
    tools=[run_procurement_tool],
)
