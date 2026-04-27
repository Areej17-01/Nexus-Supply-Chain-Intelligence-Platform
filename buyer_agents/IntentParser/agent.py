import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from buyer_agents.IntentParser.intent_tools import (
    extract_and_save_order,
    lookup_product_catalog,
    get_category_certifications,
    validate_bom_completeness,
    save_parsed_bom,
)
from google.adk.models import Gemini
from buyer_agents.IntentParser.intent_prompts import INTENT_PARSER_PROMPT
load_dotenv()

def _select_model():
    provider = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    if provider == "groq" or (not provider and os.getenv("GROQ_API_KEY")):
        return LiteLlm(
            model=os.getenv("GROQ_MODEL", "groq/llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return Gemini(model=os.getenv("INTENT_MODEL", "gemini-2.0-flash"))


gemini_model = _select_model()


intent_parser_agent = Agent(
    name="intent_parser_agent",
    model=gemini_model,
    description=(
        "Entry point for all procurement runs. Takes a raw buyer chat message, "
        "saves the order, resolves the vague product description into a specific "
        "technical BOM, validates completeness, and either saves to DB or returns "
        "clarifying questions. Passes control to Supplier Discovery Agent when ready."
    ),
    instruction=INTENT_PARSER_PROMPT,
    tools=[
        extract_and_save_order,
        lookup_product_catalog,
        get_category_certifications,
        validate_bom_completeness,
        save_parsed_bom
    ]
)

root_agent = intent_parser_agent


