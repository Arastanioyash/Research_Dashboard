from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class NPSMetrics:
    promoters: int
    passives: int
    detractors: int
    nps: int


def compute_nps(scores: Iterable[int]) -> NPSMetrics:
    cleaned = [int(s) for s in scores]
    if not cleaned:
        raise ValueError("scores cannot be empty")

    promoters = sum(1 for s in cleaned if s >= 9)
    passives = sum(1 for s in cleaned if 7 <= s <= 8)
    detractors = sum(1 for s in cleaned if s <= 6)

    total = len(cleaned)
    nps = round(((promoters / total) - (detractors / total)) * 100)

    return NPSMetrics(
        promoters=promoters, passives=passives, detractors=detractors, nps=nps
    )
