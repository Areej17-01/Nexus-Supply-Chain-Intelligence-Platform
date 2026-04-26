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

# groq_model = LiteLlm(
#     model="gemini/gemini-2.0-flash",
#     api_key=os.getenv("GEMINI_API_KEY"),
# )
gemini_model = Gemini(model="gemini-2.0-flash")


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


