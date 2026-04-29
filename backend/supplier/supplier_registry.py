"""
Supplier Registry System
Stores and manages supplier metadata, discovery, and registration.
"""

import json
from datetime import datetime
from typing import List, Optional

from nexus.core.db import get_db_conn as get_conn
from nexus.core.logger import setup_logger


log = setup_logger("nexus.supplier_registry")


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


def _normalize_json_list(raw_value) -> list:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


class SupplierRegistry:
    @staticmethod
    def register_supplier(
        supplier_id: str,
        company_name: str,
        country: str,
        region: str,
        certifications: list,
        capabilities: list,
        contact_email: str,
        api_endpoint: str = None,
        trust_score: float = 0.5,
        negotiation_style: str = "balanced",
    ) -> dict:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)
        now = datetime.utcnow().isoformat() + "Z"
        
        try:
            cur.execute(
                f"""
                SELECT id FROM suppliers WHERE id = {placeholder}
                """,
                (supplier_id,),
            )
            exists = cur.fetchone() is not None

            if exists:
                cur.execute(
                    f"""
                    UPDATE suppliers
                    SET company_name = {placeholder},
                        country = {placeholder},
                        region = {placeholder},
                        certifications = {placeholder},
                        contact_email = {placeholder},
                        api_endpoint = {placeholder},
                        trust_score = {placeholder},
                        negotiation_style = {placeholder},
                        is_active = 1,
                        updated_at = {placeholder}
                    WHERE id = {placeholder}
                    """,
                    (
                        company_name,
                        country,
                        region,
                        json.dumps(certifications or []),
                        contact_email,
                        api_endpoint,
                        trust_score,
                        negotiation_style,
                        now,
                        supplier_id,
                    ),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO suppliers
                    (id, company_name, country, region, certifications, contact_email,
                     api_endpoint, trust_score, negotiation_style, is_active, registered_at, updated_at)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                            {placeholder}, {placeholder}, {placeholder}, {placeholder}, 1, {placeholder}, {placeholder})
                    """,
                    (
                        supplier_id,
                        company_name,
                        country,
                        region,
                        json.dumps(certifications or []),
                        contact_email,
                        api_endpoint,
                        trust_score,
                        negotiation_style,
                        now,
                        now,
                    ),
                )

            conn.commit()
            return {
                "success": True,
                "supplier_id": supplier_id,
                "company_name": company_name,
                "message": "Supplier registered successfully",
                "timestamp": now,
                "capabilities": capabilities or [],
            }
        except Exception as e:
            conn.rollback()
            log.exception("register_supplier failed supplier_id=%s", supplier_id)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def add_product_to_supplier(
        supplier_id: str,
        product_id: str,
        product_name: str,
        category: str,
        unit_price: float,
        stock_quantity: int,
        lead_time_days: int,
        certifications_required: list = None,
    ) -> dict:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)

        try:
            cur.execute(
                f"""
                SELECT id FROM supplier_products
                WHERE supplier_id = {placeholder} AND product_id = {placeholder}
                """,
                (supplier_id, product_id),
            )
            exists = cur.fetchone() is not None

            if exists:
                cur.execute(
                    f"""
                    UPDATE supplier_products
                    SET product_name = {placeholder},
                        category = {placeholder},
                        unit_price = {placeholder},
                        stock_quantity = {placeholder},
                        lead_time_days = {placeholder},
                        certifications_required = {placeholder},
                        updated_at = CURRENT_TIMESTAMP
                    WHERE supplier_id = {placeholder} AND product_id = {placeholder}
                    """,
                    (
                        product_name,
                        category,
                        unit_price,
                        stock_quantity,
                        lead_time_days,
                        json.dumps(certifications_required or []),
                        supplier_id,
                        product_id,
                    ),
                )
            else:
                cur.execute(
                    f"""
                    INSERT INTO supplier_products
                    (supplier_id, product_id, product_name, category, unit_price,
                     stock_quantity, lead_time_days, certifications_required)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder},
                            {placeholder}, {placeholder}, {placeholder}, {placeholder})
                    """,
                    (
                        supplier_id,
                        product_id,
                        product_name,
                        category,
                        unit_price,
                        stock_quantity,
                        lead_time_days,
                        json.dumps(certifications_required or []),
                    ),
                )

            conn.commit()
            return {
                "success": True,
                "supplier_id": supplier_id,
                "product_id": product_id,
                "product_name": product_name,
                "message": "Product upserted into catalog",
            }
        except Exception as e:
            conn.rollback()
            log.exception("add_product_to_supplier failed supplier_id=%s product_id=%s", supplier_id, product_id)
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def discover_suppliers(
        capability: str = None,
        region: str = None,
        country: str = None,
        min_trust_score: float = 0.5,
        certifications_required: list = None,
        limit: int = 20,
    ) -> List[dict]:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)

        try:
            query = "SELECT * FROM suppliers WHERE is_active = 1"
            params = []

            if region:
                query += f" AND region = {placeholder}"
                params.append(region)

            if country:
                query += f" AND country = {placeholder}"
                params.append(country)

            if min_trust_score is not None:
                query += f" AND trust_score >= {placeholder}"
                params.append(min_trust_score)

            query += f" ORDER BY trust_score DESC LIMIT {placeholder}"
            params.append(limit)

            cur.execute(query, tuple(params))
            suppliers = cur.fetchall() or []

            if capability:
                filtered = []
                for supplier in suppliers:
                    supplier_id = _row_get(supplier, "id")
                    cur.execute(
                        f"""
                        SELECT COUNT(*) as count
                        FROM supplier_products
                        WHERE supplier_id = {placeholder} AND category = {placeholder}
                        """,
                        (supplier_id, capability),
                    )
                    count_result = cur.fetchone()
                    count_value = _row_get(count_result, "count", 0)
                    if count_value and int(count_value) > 0:
                        filtered.append(supplier)
                suppliers = filtered

            if certifications_required:
                filtered = []
                for supplier in suppliers:
                    supplier_certs = _normalize_json_list(_row_get(supplier, "certifications"))
                    if all(cert in supplier_certs for cert in certifications_required):
                        filtered.append(supplier)
                suppliers = filtered

            return [
                {
                    "supplier_id": _row_get(s, "id"),
                    "company_name": _row_get(s, "company_name"),
                    "country": _row_get(s, "country"),
                    "region": _row_get(s, "region"),
                    "certifications": _normalize_json_list(_row_get(s, "certifications")),
                    "trust_score": _row_get(s, "trust_score", 0.5),
                    "contact_email": _row_get(s, "contact_email"),
                    "api_endpoint": _row_get(s, "api_endpoint"),
                }
                for s in suppliers
            ]
        except Exception:
            log.exception(
                "discover_suppliers failed capability=%s region=%s country=%s",
                capability,
                region,
                country,
            )
            return []
        finally:
            conn.close()

    @staticmethod
    def get_supplier_by_id(supplier_id: str) -> Optional[dict]:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)

        try:
            cur.execute(
                f"SELECT * FROM suppliers WHERE id = {placeholder}",
                (supplier_id,),
            )
            supplier = cur.fetchone()
            if not supplier:
                return None

            return {
                "supplier_id": _row_get(supplier, "id"),
                "company_name": _row_get(supplier, "company_name"),
                "country": _row_get(supplier, "country"),
                "region": _row_get(supplier, "region"),
                "certifications": _normalize_json_list(_row_get(supplier, "certifications")),
                "trust_score": _row_get(supplier, "trust_score", 0.5),
                "contact_email": _row_get(supplier, "contact_email"),
                "api_endpoint": _row_get(supplier, "api_endpoint"),
                "negotiation_style": _row_get(supplier, "negotiation_style", "balanced"),
                "is_active": _row_get(supplier, "is_active", 1),
                "registered_at": _row_get(supplier, "registered_at"),
            }
        except Exception:
            log.exception("get_supplier_by_id failed supplier_id=%s", supplier_id)
            return None
        finally:
            conn.close()

    @staticmethod
    def update_supplier_trust_score(
        supplier_id: str,
        adjustment: float,
        reason: str = None,
    ) -> dict:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)

        try:
            cur.execute(
                f"SELECT trust_score FROM suppliers WHERE id = {placeholder}",
                (supplier_id,),
            )
            result = cur.fetchone()
            if not result:
                return {"error": "Supplier not found"}

            current_score = float(_row_get(result, "trust_score", 0.5))
            new_score = max(0.0, min(1.0, current_score + adjustment))

            cur.execute(
                f"""
                UPDATE suppliers
                SET trust_score = {placeholder}, updated_at = CURRENT_TIMESTAMP
                WHERE id = {placeholder}
                """,
                (new_score, supplier_id),
            )
            conn.commit()

            return {
                "success": True,
                "supplier_id": supplier_id,
                "previous_score": current_score,
                "new_score": new_score,
                "adjustment": adjustment,
                "reason": reason,
            }
        except Exception as e:
            conn.rollback()
            log.exception("update_supplier_trust_score failed supplier_id=%s", supplier_id)
            return {"error": str(e)}
        finally:
            conn.close()

    @staticmethod
    def list_all_suppliers(limit: int = 100) -> List[dict]:
        conn = get_conn()
        cur = conn.cursor()
        placeholder = _ph(conn)

        try:
            cur.execute(
                f"""
                SELECT * FROM suppliers
                WHERE is_active = 1
                ORDER BY trust_score DESC
                LIMIT {placeholder}
                """,
                (limit,),
            )
            suppliers = cur.fetchall() or []

            return [
                {
                    "supplier_id": _row_get(s, "id"),
                    "company_name": _row_get(s, "company_name"),
                    "country": _row_get(s, "country"),
                    "region": _row_get(s, "region"),
                    "trust_score": _row_get(s, "trust_score", 0.5),
                    "certifications": _normalize_json_list(_row_get(s, "certifications")),
                }
                for s in suppliers
            ]
        except Exception:
            log.exception("list_all_suppliers failed")
            return []
        finally:
            conn.close()
