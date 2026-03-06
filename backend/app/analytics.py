from __future__ import annotations

from typing import Iterable


def infer_schema(rows: list[dict[str, str]]) -> dict[str, str]:
    """Infer a lightweight schema from tabular row data.

    Returns per-column type as one of: integer, float, boolean, string.
    """
    schema: dict[str, str] = {}
    for row in rows:
        for key, value in row.items():
            current = schema.get(key)
            detected = _detect_type(value)
            schema[key] = _merge_types(current, detected)
    return schema


def compute_single_select_mean(
    responses: Iterable[str], score_map: dict[str, float]
) -> float:
    """Compute mean score for a single-select question.

    Unknown or blank responses are ignored.
    """
    scores: list[float] = []
    for response in responses:
        if response in score_map:
            scores.append(float(score_map[response]))

    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def _detect_type(raw: str | None) -> str:
    if raw is None:
        return "string"

    value = str(raw).strip()
    if value == "":
        return "string"
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return "boolean"

    try:
        int(value)
        return "integer"
    except ValueError:
        pass

    try:
        float(value)
        return "float"
    except ValueError:
        return "string"


def _merge_types(current: str | None, incoming: str) -> str:
    if current is None:
        return incoming
    if current == incoming:
        return current

    numeric = {"integer", "float"}
    if current in numeric and incoming in numeric:
        return "float"

    if current == "string" or incoming == "string":
        return "string"

    return "string"
