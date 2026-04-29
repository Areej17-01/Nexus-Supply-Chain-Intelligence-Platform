import json
from typing import List, Optional

from pydantic import BaseModel

from nexus.core.db import get_db_conn as get_conn
from nexus.core.logger import setup_logger

log = setup_logger("nexus.registry")


class AgentCard(BaseModel):
    id: str
    name: str
    role: str = "supplier"
    capabilities: List[str] = []
    region: str
    country: Optional[str] = None
    certifications: List[str] = []
    trust_score: float = 0.5
    endpoint: Optional[str] = None


def _is_sqlite_conn(conn) -> bool:
    return conn.__class__.__module__.startswith("sqlite3")


def _ph(conn) -> str:
    return "?" if _is_sqlite_conn(conn) else "%s"


def _row_get(row, key, default=None):
    if row is None:
        return default
    try:
        return row.get(key, default)
    except Exception:
        pass
    try:
        return row[key]
    except Exception:
        return default


def _json_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


class AgentRegistry:
    def list_agents(self, role: str = None, region: str = None, capability: str = None, min_trust: float = 0.0) -> list:
        return self.discover(role=role, region=region, capability=capability, min_trust=min_trust, limit=100)

    def discover(
        self,
        role: str = "supplier",
        capability: str = None,
        region: str = None,
        min_trust: float = 0.0,
        limit: int = 5,
    ) -> list:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)
        try:
            query = "SELECT * FROM suppliers WHERE is_active = 1 AND trust_score >= " + placeholder
            params = [min_trust]
            if region and region != "ANY":
                query += " AND region = " + placeholder
                params.append(region)
            query += " ORDER BY trust_score DESC LIMIT " + placeholder
            params.append(max(limit * 3, limit))
            cur.execute(query, tuple(params))
            rows = cur.fetchall() or []

            agents = []
            for row in rows:
                supplier_id = _row_get(row, "id")
                capabilities = self._capabilities_for_supplier(cur, supplier_id, placeholder)
                if capability and capability not in capabilities:
                    continue
                agents.append(
                    AgentCard(
                        id=supplier_id,
                        name=_row_get(row, "company_name"),
                        role=role or "supplier",
                        capabilities=capabilities,
                        region=_row_get(row, "region"),
                        country=_row_get(row, "country"),
                        certifications=_json_list(_row_get(row, "certifications")),
                        trust_score=float(_row_get(row, "trust_score", 0.5) or 0.5),
                        endpoint=_row_get(row, "api_endpoint") or f"internal://supplier/{supplier_id}",
                    ).model_dump()
                )
                if len(agents) >= limit:
                    break
            return agents
        except Exception:
            log.exception("Registry discover failed role=%s capability=%s region=%s", role, capability, region)
            return []
        finally:
            conn.close()

    def get_supplier(self, supplier_id: str) -> Optional[dict]:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)
        try:
            cur.execute(f"SELECT * FROM suppliers WHERE id = {placeholder}", (supplier_id,))
            supplier = cur.fetchone()
            if not supplier:
                return None
            card = AgentCard(
                id=_row_get(supplier, "id"),
                name=_row_get(supplier, "company_name"),
                role="supplier",
                capabilities=self._capabilities_for_supplier(cur, supplier_id, placeholder),
                region=_row_get(supplier, "region"),
                country=_row_get(supplier, "country"),
                certifications=_json_list(_row_get(supplier, "certifications")),
                trust_score=float(_row_get(supplier, "trust_score", 0.5) or 0.5),
                endpoint=_row_get(supplier, "api_endpoint") or f"internal://supplier/{supplier_id}",
            ).model_dump()
            card["negotiation_style"] = _row_get(supplier, "negotiation_style", "balanced")
            return card
        except Exception:
            log.exception("Registry get_supplier failed supplier_id=%s", supplier_id)
            return None
        finally:
            conn.close()

    def _capabilities_for_supplier(self, cur, supplier_id: str, placeholder: str) -> list:
        cur.execute(
            f"SELECT DISTINCT category FROM supplier_products WHERE supplier_id = {placeholder}",
            (supplier_id,),
        )
        return [_row_get(row, "category") for row in (cur.fetchall() or []) if _row_get(row, "category")]
