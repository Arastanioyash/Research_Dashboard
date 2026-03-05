from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class InferenceResult:
    major_type: str
    subtype: str


def _normalized(values: Iterable[object]) -> List[str]:
    return [
        str(v).strip().lower() for v in values if v is not None and str(v).strip() != ""
    ]


def infer_question_types(
    columns: Dict[str, Iterable[object]],
) -> Dict[str, InferenceResult]:
    """Infer a major_type/subtype for each survey column.

    Rules are intentionally simple and deterministic for unit-testable behavior.
    """
    inferred: Dict[str, InferenceResult] = {}

    for name, raw_values in columns.items():
        values = _normalized(raw_values)

        if not values:
            inferred[name] = InferenceResult("unknown", "empty")
            continue

        if any(k in name.lower() for k in ["text", "comment", "open", "freeform"]):
            inferred[name] = InferenceResult("text", "open_ended")
            continue

        uniques = set(values)

        if uniques.issubset({"0", "1", "true", "false", "yes", "no"}):
            if len(uniques) > 1:
                inferred[name] = InferenceResult("choice", "multi_select_binary")
            else:
                inferred[name] = InferenceResult("unknown", "constant_binary")
            continue

        if all(v.isdigit() for v in values):
            nums = [int(v) for v in values]
            min_v, max_v = min(nums), max(nums)

            if min_v >= 0 and max_v <= 10 and "nps" in name.lower():
                inferred[name] = InferenceResult("metric", "nps")
            elif (
                min_v >= 1
                and max_v <= 5
                and any(k in name.lower() for k in ["likert", "grid"])
            ):
                inferred[name] = InferenceResult("choice", "grid_likert")
            elif min_v >= 1 and max_v <= 10 and "rank" in name.lower():
                inferred[name] = InferenceResult("choice", "ranking")
            elif max_v <= 100 and "sum" in name.lower():
                inferred[name] = InferenceResult("metric", "constant_sum")
            else:
                inferred[name] = InferenceResult("metric", "numeric")
            continue

        if len(uniques) <= 8:
            inferred[name] = InferenceResult("choice", "single_select")
        else:
            inferred[name] = InferenceResult("unknown", "unclassified")

    return inferred
