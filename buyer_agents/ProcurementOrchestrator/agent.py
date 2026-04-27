import os
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.models.lite_llm import LiteLlm

from buyer_agents.ProcurementOrchestrator.prompts import (
    ORCHESTRATOR_PROMPT,
    INTENT_PARSER_PROMPT,
    SUPPLIER_DISCOVERY_PROMPT,
    MACRO_INTELLIGENCE_PROMPT,
    RISK_ASSESSMENT_PROMPT,
    NEGOTIATION_PROMPT,
)
from buyer_agents.ProcurementOrchestrator.tools import (
    parse_intent_and_create_order,
    discover_suppliers_for_line_item,
    get_macro_context,
    assess_supplier_risk,
    create_negotiation_strategy,
    select_supplier_for_line_item,
)

def _select_model():
    provider = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    if provider == "groq" or (not provider and os.getenv("GROQ_API_KEY")):
        return LiteLlm(
            model=os.getenv("GROQ_MODEL", "groq/llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return Gemini(model=os.getenv("ORCHESTRATOR_MODEL", "gemini-2.0-flash"))


model = _select_model()


intent_parser_agent = Agent(
    name="procurement_intent_parser_agent",
    model=model,
    description="Parses buyer request and creates structured order records.",
    instruction=INTENT_PARSER_PROMPT,
    tools=[parse_intent_and_create_order],
)

supplier_discovery_agent = Agent(
    name="supplier_discovery_agent",
    model=model,
    description="Finds and ranks suppliers for parsed BOM requirements.",
    instruction=SUPPLIER_DISCOVERY_PROMPT,
    tools=[discover_suppliers_for_line_item, select_supplier_for_line_item],
)

macro_intelligence_agent = Agent(
    name="macro_intelligence_agent",
    model=model,
    description="Pulls active macro signals and negotiation implications.",
    instruction=MACRO_INTELLIGENCE_PROMPT,
    tools=[get_macro_context],
)

risk_assessment_agent = Agent(
    name="risk_assessment_agent",
    model=model,
    description="Scores supplier risk and flags blockers.",
    instruction=RISK_ASSESSMENT_PROMPT,
    tools=[assess_supplier_risk],
)

negotiation_agent = Agent(
    name="negotiation_agent",
    model=model,
    description="Generates buyer-safe negotiation strategy and HITL escalation.",
    instruction=NEGOTIATION_PROMPT,
    tools=[create_negotiation_strategy],
)

root_agent = Agent(
    name="buyer_procurement_orchestrator",
    model=model,
    description="Coordinates full buyer procurement flow from intent to negotiation strategy.",
    instruction=ORCHESTRATOR_PROMPT,
    sub_agents=[
        intent_parser_agent,
        supplier_discovery_agent,
        macro_intelligence_agent,
        risk_assessment_agent,
        negotiation_agent,
    ],
)

