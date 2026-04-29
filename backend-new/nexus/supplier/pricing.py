from __future__ import annotations

import json
from typing import Tuple


def _get_price_map(raw: str) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def get_base_and_floor(base_map: str, floor_map: str, category: str) -> Tuple[float, float]:
    base_prices = _get_price_map(base_map)
    floor_prices = _get_price_map(floor_map)
    base = float(base_prices.get(category, base_prices.get("default", 0.0)))
    floor = float(floor_prices.get(category, floor_prices.get("default", 0.0)))
    return base, floor


def calculate_unit_price(base_price: float, quantity: int) -> Tuple[float, float]:
    if quantity >= 1000:
        discount = 0.15
    elif quantity >= 500:
        discount = 0.10
    elif quantity >= 100:
        discount = 0.05
    else:
        discount = 0.0
    unit_price = round(base_price * (1 - discount), 2)
    return unit_price, discount
