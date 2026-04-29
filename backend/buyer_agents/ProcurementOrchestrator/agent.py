import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .prompts import ORCHESTRATOR_PROMPT
from .tools import (
    auto_select_supplier_for_line_item,
    create_negotiation_strategy,
    create_purchase_order,
    generate_contract_text,
    get_macro_risk_bundle,
    parse_intent_and_create_order,
    persist_negotiation_round,
    send_message_to_supplier,
    send_rfq_to_supplier,
)
from nexus.core.logger import setup_logger

log = setup_logger("procurement_orchestrator.agent")


def _select_model():
    """Prefer Gemini. Only use Groq if explicitly requested via LLM_PROVIDER=groq."""

    provider = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    if provider == "groq":
        from google.adk.models.lite_llm import LiteLlm

        return LiteLlm(
            model=os.getenv("GROQ_MODEL", "groq/llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )

    gemini_model = (
        os.getenv("GEMINI_MODEL")
        or os.getenv("ORCHESTRATOR_MODEL")
        or "gemini-2.0-flash"
    )
    attempts = int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))
    initial_delay = float(os.getenv("LLM_RETRY_INITIAL_DELAY", "30"))
    return Gemini(
        model=gemini_model,
        retry_options=types.HttpRetryOptions(initial_delay=initial_delay, attempts=attempts),
    )


model = _select_model()
log.info("ProcurementOrchestrator initialized with model=%s", getattr(model, "model", type(model).__name__))


# Root orchestrator: single LLM agent + deterministic tools to reduce LLM turns.
root_agent = Agent(
    name="buyer_procurement_orchestrator",
    model=model,
    description="Coordinates the procurement flow end-to-end using tools (minimizing LLM turns).",
    instruction=ORCHESTRATOR_PROMPT,
    tools=[
        # 1) Intent parsing (LLM decides inputs, tool persists)
        parse_intent_and_create_order,
        # 2) Deterministic supplier selection
        auto_select_supplier_for_line_item,
        # 3) Deterministic macro + risk bundle
        get_macro_risk_bundle,
        # 4) Negotiation tools (multi-turn with supplier agent)
        create_negotiation_strategy,
        send_rfq_to_supplier,
        send_message_to_supplier,
        persist_negotiation_round,
        # 5) Deterministic contract drafting + persistence
        generate_contract_text,
        create_purchase_order,
    ],
)
