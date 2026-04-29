"""
Supplier Quote Agent
Google ADK agent for responding to RFQ requests
"""


import os
from functools import cached_property

from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from nexus.core.logger import setup_logger

from supplier.QuoteAgent.supplier_tools import (
    get_supplier_catalog,
    check_inventory,
    calculate_quote,
    validate_buyer_requirements,
    save_quote_to_db,
)
from supplier.QuoteAgent.supplier_prompts import SUPPLIER_QUOTE_AGENT_PROMPT

load_dotenv()
log = setup_logger("supplier.quote_agent")


class _SupplierGemini(Gemini):
    """Gemini variant that uses SUPPLIER_GEMINI_API_KEY when available,
    keeping supplier and buyer calls on separate rate-limit buckets."""

    @cached_property
    def api_client(self):
        from google.genai import Client

        api_key = os.getenv("SUPPLIER_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
            ),
        )


_gemini_model_name = (
    os.getenv("SUPPLIER_MODEL")
    or os.getenv("GEMINI_MODEL")
    or "gemini-2.0-flash"
)

attempts = int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))
initial_delay = float(os.getenv("LLM_RETRY_INITIAL_DELAY", "30"))

gemini_model = _SupplierGemini(
    model=_gemini_model_name,
    retry_options=types.HttpRetryOptions(initial_delay=initial_delay, attempts=attempts),
)

log.info("QuoteAgent initialized with model=%s", _gemini_model_name)




def create_supplier_agent(supplier_id: str) -> Agent:
    """
    Factory function to create a supplier agent instance.
    
    Args:
        supplier_id: The supplier's unique ID (e.g., 'supplier-001')
    
    Returns:
        Configured Google ADK Agent instance for quote generation
    """
    
    # Create agent-specific tools that are bound to this supplier
    def get_catalog_tool() -> dict:
        """Get this supplier's catalog"""
        return get_supplier_catalog(supplier_id)
    
    def check_inventory_tool(product_id: str, quantity_needed: int) -> dict:
        """Check inventory for a specific product"""
        return check_inventory(supplier_id, product_id, quantity_needed)
    
    def validate_requirements_tool(
        required_certifications: list,
        delivery_region: str,
        lead_time_days: int
    ) -> dict:
        """Validate buyer requirements"""
        return validate_buyer_requirements(
            supplier_id,
            required_certifications,
            delivery_region,
            lead_time_days
        )
    
    def calculate_quote_tool(
        items: list,
        buyer_id: str = None,
        negotiation_style: str = "balanced"
    ) -> dict:
        """Calculate quote for requested items"""
        return calculate_quote(
            supplier_id,
            items,
            buyer_id,
            negotiation_style
        )
    
    def save_quote_tool(quote_data: dict, order_id: str = None) -> dict:
        """Save the quote to database"""
        return save_quote_to_db(supplier_id, quote_data, order_id)
    
# Create the agent
QuoteAgent = Agent(
    name="QuoteAgent",
    model=gemini_model,
    description=(
        "Responds to buyer RFQ (Request for Quote) requests. "
        "Checks inventory, validates requirements, generates quotes, "
        "and handles negotiation on behalf of the supplier."
    ),
    instruction=SUPPLIER_QUOTE_AGENT_PROMPT,
    tools=[
        get_supplier_catalog,
        check_inventory,
        validate_buyer_requirements,
        calculate_quote,
        save_quote_to_db,
    ]
)

# ADK looks for 'root_agent'
root_agent = QuoteAgent

def get_supplier_agent(supplier_id: str) -> Agent:
    # Factory logic is handled by ADK's runtime, but we keep this for local calls
    return QuoteAgent

