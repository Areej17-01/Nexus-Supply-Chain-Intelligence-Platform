from __future__ import annotations

from nexus.database import SupplierRLStats, get_db_session


def choose_discount(supplier_id: str) -> float:
    with get_db_session() as db:
        stats = db.query(SupplierRLStats).filter(SupplierRLStats.supplier_id == supplier_id).first()
        if not stats:
            return 0.15
        if (stats.negotiations or 0) < 5:
            return 0.15

        avg_discount_achieved = (stats.total_discount_achieved or 0.0) / max(stats.negotiations or 0, 1)
        opening = min(avg_discount_achieved * 1.2, stats.max_discount_seen or 0.0, 0.30)
        return float(opening)


def record_outcome(supplier_id: str, discount_asked: float, discount_achieved: float) -> None:
    with get_db_session() as db:
        stats = db.query(SupplierRLStats).filter(SupplierRLStats.supplier_id == supplier_id).first()
        if not stats:
            stats = SupplierRLStats(supplier_id=supplier_id)
            db.add(stats)
            db.flush()

        stats.negotiations = (stats.negotiations or 0) + 1
        stats.total_discount_achieved = (stats.total_discount_achieved or 0.0) + float(discount_achieved)
        stats.max_discount_seen = max(stats.max_discount_seen or 0.0, float(discount_achieved))

        if float(discount_achieved) >= float(discount_asked) * 0.8:
            stats.best_opening_ask = float(discount_asked)

        db.commit()
