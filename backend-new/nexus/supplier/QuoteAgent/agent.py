import json
import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types as genai_types

from nexus.supplier.tools import route_message

logger = logging.getLogger(__name__)


class QuoteAgentImpl(BaseAgent):
    """Deterministic supplier agent — routes RFQ/counter_offer without an LLM."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        user_text = ""
        if ctx.user_content and ctx.user_content.parts:
            for part in ctx.user_content.parts:
                if hasattr(part, "text") and part.text:
                    user_text = part.text
                    break

        try:
            msg_type = json.loads(user_text).get("type") if user_text else "unknown"
            result = await route_message(user_text)
            result_text = json.dumps(result) if not isinstance(result, str) else result
            logger.info("QuoteAgent routed type=%s", msg_type)
        except Exception as exc:
            logger.exception("QuoteAgent error: %s", exc)
            result_text = json.dumps({"error": str(exc)})

        yield Event(
            author=self.name,
            content=genai_types.Content(
                role="model",
                parts=[genai_types.Part(text=result_text)],
            ),
        )


root_agent = QuoteAgentImpl(
    name="QuoteAgent",
    description="Handles RFQ and negotiation messages for supplier quotes.",
)
