from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RLUpdateResult:
    reward: float
    new_trust: float
    new_fit: float
    success_rate: float


def compute_reward(outcome: str, discount_given: float, rounds_taken: int, max_rounds: int) -> float:
    if outcome == "accepted":
        efficiency_bonus = 1.0 - (rounds_taken / max_rounds)
        price_bonus = min(discount_given / 0.20, 1.0)
        reward = 0.6 + (0.2 * efficiency_bonus) + (0.2 * price_bonus)
    elif outcome == "walkaway":
        reward = 0.2
    else:
        reward = 0.0
    return min(reward, 1.0)


def update_scores(old_trust: float, total_deals: int, successful_deals: int, reward: float, outcome: str) -> RLUpdateResult:
    alpha = 0.15
    new_trust = (1 - alpha) * old_trust + alpha * reward
    total_deals += 1
    if outcome == "accepted":
        successful_deals += 1
    success_rate = successful_deals / total_deals
    new_fit = (0.5 * new_trust) + (0.5 * success_rate)
    return RLUpdateResult(
        reward=round(reward, 4),
        new_trust=round(new_trust, 4),
        new_fit=round(new_fit, 4),
        success_rate=round(success_rate, 4),
    )
