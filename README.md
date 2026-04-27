# Nexus-Supply-Chain-Intelligence-Platform
NEXUS is a supply chain coordination platform where AI agents do the hard work of finding suppliers, negotiating prices, checking compliance, and actually closing the deal with contract.

## Buyer Agent Stack

The app now includes a full buyer-side multi-agent flow:

1. `Procurement Intent Parser` - parses buyer request and creates structured order records.
2. `Supplier Discovery Agent` - finds and ranks matching suppliers from catalog/trust/relationship data.
3. `Macro Intelligence Agent` - injects active macro signals relevant to category and region.
4. `Risk Assessment Agent` - scores supplier risk and identifies blockers.
5. `Negotiation Agent` - creates negotiation strategy with HITL escalation logic.

Root orchestrator: `buyer_agents/ProcurementOrchestrator/agent.py`

## Run

- Start server: `uv run python main.py`
- API host: `http://0.0.0.0:8010`
- A2A mode: enabled in `main.py`

## Session API Behavior

- `user_id` in `/run` is used as the session user identifier.
- `session_id` keeps conversation continuity for that user/app pair.
- The app logs `app_name`, `user_id`, and `session_id` for `/run` requests.

## Run Agents on Different Ports

Use `run_agent.py` to run each agent independently:

- IntentParser on `8011`:
  - `set AGENT_NAME=IntentParser && set PORT=8011 && uv run python run_agent.py`
- SupplierDiscovery on `8012`:
  - `set AGENT_NAME=SupplierDiscovery && set PORT=8012 && uv run python run_agent.py`
- MacroIntelligence on `8013`:
  - `set AGENT_NAME=MacroIntelligence && set PORT=8013 && uv run python run_agent.py`
- RiskAssessment on `8014`:
  - `set AGENT_NAME=RiskAssessment && set PORT=8014 && uv run python run_agent.py`
- Negotiation on `8015`:
  - `set AGENT_NAME=Negotiation && set PORT=8015 && uv run python run_agent.py`
- Full ProcurementOrchestrator on `8010`:
  - `set AGENT_NAME=ProcurementOrchestrator && set PORT=8010 && uv run python run_agent.py`

You can keep using the single multi-app endpoint in `main.py` with:
- `POST /run` + `app_name`
- `GET /apps/{app_name}/users/{user_id}/sessions`

