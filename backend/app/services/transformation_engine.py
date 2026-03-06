"""Survey transformation engine.

This module normalizes raw survey exports into a star-schema-like set of parquet tables
for analytics workloads.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


MISSING_CODE_DEFAULTS = {"", "na", "n/a", "dk", "dont know", "don't know", "refused", "missing", "99", "999", "-99", "-999"}
TEXT_TYPE_HINTS = {"text", "open", "open_ended", "oe", "verbatim", "string", "unknown"}
VALUE_TYPE_HINTS = {"numeric", "number", "scale", "rating", "constant_sum", "ranking", "rank"}
CHOICE_TYPE_HINTS = {"single_select", "single", "radio", "multi_select", "multi", "checkbox", "nps", "grid", "multi_grid", "matrix"}


@dataclass
class CodeSpec:
    value: str
    text: str
    is_missing: bool = False


@dataclass
class ItemSpec:
    key: str
    text: str
    column: str
    type_override: str | None = None


@dataclass
class QuestionSpec:
    question_id: str
    text: str
    qtype: str
    group: str | None = None
    columns: list[str] = field(default_factory=list)
    items: list[ItemSpec] = field(default_factory=list)
    codes: list[CodeSpec] = field(default_factory=list)
    ignored_for_compute: bool = False
    is_open_ended: bool = False


@dataclass
class BannerSpec:
    banner_id: str
    text: str
    column: str


def transform_project(project_id: str, raw_csv_path: str, metadata_path: str, banner_metadata_path: str, model_version: str) -> dict[str, str]:
    """Transform a project export into parquet dimensions/facts and schema registry JSON."""

    raw_df = pd.read_csv(raw_csv_path)
    question_specs = _parse_question_specs(metadata_path)
    banners = _parse_banner_specs(banner_metadata_path)

    respondent_col = _detect_respondent_col(raw_df)
    weight_col = _detect_weight_col(raw_df)

    question_specs = _augment_with_open_ended_detection(raw_df, question_specs, respondent_col, weight_col, banners)

    out_dir = Path(raw_csv_path).resolve().parent / f"{project_id}_transformed"
    out_dir.mkdir(parents=True, exist_ok=True)

    dim_respondent = _build_dim_respondent(raw_df, respondent_col, weight_col, banners)
    dim_question = _build_dim_question(question_specs)
    dim_item = _build_dim_item(question_specs)
    dim_code = _build_dim_code(question_specs)
    code_lookup = {
        (row["question_id"], row["item_id"], str(row["code_value"])): row["code_id"]
        for _, row in dim_code.iterrows()
    }
    missing_lookup = {
        (row["question_id"], row["item_id"], str(row["code_value"])): bool(row["is_missing"]) for _, row in dim_code.iterrows()
    }

    fact_choice, fact_value = _build_facts(raw_df, respondent_col, weight_col, question_specs, code_lookup, missing_lookup)

    schema_registry = _build_schema_registry(project_id, model_version, question_specs, banners)

    dim_respondent.to_parquet(out_dir / "dim_respondent.parquet", index=False)
    dim_question.to_parquet(out_dir / "dim_question.parquet", index=False)
    dim_item.to_parquet(out_dir / "dim_item.parquet", index=False)
    dim_code.to_parquet(out_dir / "dim_code.parquet", index=False)
    fact_choice.to_parquet(out_dir / "fact_choice.parquet", index=False)
    fact_value.to_parquet(out_dir / "fact_value.parquet", index=False)
    (out_dir / "schema_registry.json").write_text(json.dumps(schema_registry, indent=2), encoding="utf-8")

    return {
        "output_dir": str(out_dir),
        "dim_respondent": str(out_dir / "dim_respondent.parquet"),
        "dim_question": str(out_dir / "dim_question.parquet"),
        "dim_item": str(out_dir / "dim_item.parquet"),
        "dim_code": str(out_dir / "dim_code.parquet"),
        "fact_choice": str(out_dir / "fact_choice.parquet"),
        "fact_value": str(out_dir / "fact_value.parquet"),
        "schema_registry": str(out_dir / "schema_registry.json"),
    }


def _read_metadata(path: str) -> Any:
    p = Path(path)
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))

    df = pd.read_csv(path)
    return df.to_dict(orient="records")


def _normalize_qtype(raw_type: str | None) -> str:
    token = (raw_type or "unknown").strip().lower().replace("-", "_").replace(" ", "_")
    if token in {"matrix", "grid"}:
        return "grid"
    if token in {"multigrid", "multi_grid", "multi_matrix"}:
        return "multi_grid"
    if token in {"single", "singlechoice", "single_select", "radio"}:
        return "single_select"
    if token in {"multi", "multiselect", "multi_select", "checkbox"}:
        return "multi_select"
    if token in {"nps", "net_promoter_score"}:
        return "nps"
    if token in {"rank", "ranking"}:
        return "ranking"
    if token in {"constant_sum", "constantsum"}:
        return "constant_sum"
    if token in {"number", "numeric", "scale", "rating"}:
        return "numeric"
    if token in TEXT_TYPE_HINTS:
        return "text"
    return token or "unknown"


def _parse_question_specs(metadata_path: str) -> list[QuestionSpec]:
    payload = _read_metadata(metadata_path)
    questions_raw = payload.get("questions", payload) if isinstance(payload, dict) else payload

    specs: list[QuestionSpec] = []
    for row in questions_raw:
        qid = str(row.get("id") or row.get("question_id") or row.get("name"))
        if not qid:
            continue

        qtype = _normalize_qtype(row.get("type"))
        columns = row.get("columns") or row.get("column") or []
        if isinstance(columns, str):
            columns = [columns]

        items_raw = row.get("items") or []
        items: list[ItemSpec] = []
        for idx, item in enumerate(items_raw):
            col = item.get("column") or (columns[idx] if idx < len(columns) else None)
            if not col:
                continue
            items.append(
                ItemSpec(
                    key=str(item.get("id") or item.get("key") or f"{qid}_item_{idx + 1}"),
                    text=str(item.get("text") or item.get("label") or item.get("id") or col),
                    column=str(col),
                    type_override=_normalize_qtype(item.get("type")) if item.get("type") else None,
                )
            )

        if not items and columns:
            items = [ItemSpec(key=f"{qid}_item_1", text=str(row.get("text") or qid), column=str(columns[0]))]

        codes_raw = row.get("codes") or []
        missing_codes = {str(v).strip().lower() for v in row.get("missing_codes", [])}
        codes: list[CodeSpec] = []
        for code in codes_raw:
            value = str(code.get("value") if isinstance(code, dict) else code)
            text = str(code.get("text") if isinstance(code, dict) else code)
            is_missing = str(value).strip().lower() in missing_codes or str(text).strip().lower() in missing_codes
            codes.append(CodeSpec(value=value, text=text, is_missing=is_missing))

        specs.append(
            QuestionSpec(
                question_id=qid,
                text=str(row.get("text") or row.get("label") or qid),
                qtype=qtype,
                group=row.get("group") or row.get("section"),
                columns=[str(c) for c in columns],
                items=items,
                codes=codes,
                ignored_for_compute=bool(row.get("ignored_for_compute", False)),
                is_open_ended=qtype in {"text", "unknown"},
            )
        )

    return specs


def _parse_banner_specs(path: str) -> list[BannerSpec]:
    payload = _read_metadata(path)
    rows = payload.get("banners", payload) if isinstance(payload, dict) else payload
    specs: list[BannerSpec] = []
    for idx, row in enumerate(rows):
        col = row.get("column") or row.get("name")
        if not col:
            continue
        specs.append(
            BannerSpec(
                banner_id=str(row.get("id") or f"banner_{idx + 1}"),
                text=str(row.get("text") or row.get("label") or col),
                column=str(col),
            )
        )
    return specs


def _detect_respondent_col(df: pd.DataFrame) -> str:
    for c in ["respondent_id", "response_id", "id", "record_id"]:
        if c in df.columns:
            return c
    return df.columns[0]


def _detect_weight_col(df: pd.DataFrame) -> str | None:
    for c in ["weight", "final_weight", "wgt"]:
        if c in df.columns:
            return c
    return None


def _augment_with_open_ended_detection(
    df: pd.DataFrame,
    specs: list[QuestionSpec],
    respondent_col: str,
    weight_col: str | None,
    banners: list[BannerSpec],
) -> list[QuestionSpec]:
    mapped_cols = {respondent_col}
    if weight_col:
        mapped_cols.add(weight_col)
    mapped_cols.update(b.column for b in banners)
    for spec in specs:
        mapped_cols.update(spec.columns)
        mapped_cols.update(item.column for item in spec.items)

    for col in df.columns:
        if col in mapped_cols:
            continue
        series = df[col]
        looks_text = pd.api.types.is_string_dtype(series) or series.dtype == object
        if looks_text:
            specs.append(
                QuestionSpec(
                    question_id=col,
                    text=col,
                    qtype="text",
                    group="auto_detected",
                    columns=[col],
                    items=[ItemSpec(key=f"{col}_item_1", text=col, column=col)],
                    codes=[],
                    ignored_for_compute=True,
                    is_open_ended=True,
                )
            )
    return specs


def _build_dim_respondent(df: pd.DataFrame, respondent_col: str, weight_col: str | None, banners: list[BannerSpec]) -> pd.DataFrame:
    out = pd.DataFrame({"respondent_id": df[respondent_col].astype(str)})
    for banner in banners:
        out[banner.column] = df[banner.column].astype(str) if banner.column in df.columns else None
    if weight_col and weight_col in df.columns:
        out["weight"] = pd.to_numeric(df[weight_col], errors="coerce").fillna(1.0)
    else:
        out["weight"] = 1.0
    return out


def _build_dim_question(specs: list[QuestionSpec]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "question_id": s.question_id,
                "question_text": s.text,
                "question_type": s.qtype,
                "question_group": s.group,
                "ignored_for_compute": s.ignored_for_compute,
                "is_open_ended": s.is_open_ended,
            }
            for s in specs
        ]
    )


def _build_dim_item(specs: list[QuestionSpec]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for s in specs:
        for idx, item in enumerate(s.items or [ItemSpec(key=f"{s.question_id}_item_1", text=s.text, column=s.columns[0])]):
            rows.append(
                {
                    "item_id": f"{s.question_id}::{item.key or idx + 1}",
                    "question_id": s.question_id,
                    "item_key": item.key,
                    "item_text": item.text,
                    "column": item.column,
                }
            )
    return pd.DataFrame(rows)


def _build_dim_code(specs: list[QuestionSpec]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for s in specs:
        item_list = s.items or [ItemSpec(key=f"{s.question_id}_item_1", text=s.text, column=s.columns[0] if s.columns else s.question_id)]
        if not s.codes and s.qtype in CHOICE_TYPE_HINTS:
            # preserve metadata even when not explicitly provided
            s.codes = []
        for item in item_list:
            for code in s.codes:
                rows.append(
                    {
                        "code_id": f"{s.question_id}::{item.key}::{code.value}",
                        "question_id": s.question_id,
                        "item_id": f"{s.question_id}::{item.key}",
                        "code_value": str(code.value),
                        "code_text": code.text,
                        "is_missing": bool(code.is_missing) or str(code.value).strip().lower() in MISSING_CODE_DEFAULTS,
                    }
                )
    return pd.DataFrame(rows)


def _split_multiselect(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    chunks = re.split(r"[|;,]", str(value))
    return [c.strip() for c in chunks if c.strip()]


def _build_facts(
    df: pd.DataFrame,
    respondent_col: str,
    weight_col: str | None,
    specs: list[QuestionSpec],
    code_lookup: dict[tuple[str, str, str], str],
    missing_lookup: dict[tuple[str, str, str], bool],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    choice_rows: list[dict[str, Any]] = []
    value_rows: list[dict[str, Any]] = []

    weights = pd.to_numeric(df[weight_col], errors="coerce").fillna(1.0) if weight_col and weight_col in df.columns else pd.Series(1.0, index=df.index)

    for s in specs:
        item_list = s.items or [ItemSpec(key=f"{s.question_id}_item_1", text=s.text, column=s.columns[0] if s.columns else s.question_id)]
        for item in item_list:
            if item.column not in df.columns:
                continue

            item_id = f"{s.question_id}::{item.key}"
            for idx, raw in df[item.column].items():
                respondent_id = str(df.at[idx, respondent_col])
                weight = float(weights.at[idx])

                qtype = item.type_override or s.qtype
                if qtype in {"single_select", "nps", "grid"}:
                    if pd.isna(raw) or str(raw).strip() == "":
                        continue
                    code_value = str(raw).strip()
                    is_missing = missing_lookup.get((s.question_id, item_id, code_value), code_value.strip().lower() in MISSING_CODE_DEFAULTS)
                    choice_rows.append(
                        {
                            "respondent_id": respondent_id,
                            "question_id": s.question_id,
                            "item_id": item_id,
                            "code_id": code_lookup.get((s.question_id, item_id, code_value)),
                            "code_value": code_value,
                            "selected": True,
                            "weight": weight,
                            "compute_in_base": not is_missing and not s.ignored_for_compute,
                        }
                    )
                elif qtype in {"multi_select", "multi_grid"}:
                    for code_value in _split_multiselect(raw):
                        is_missing = missing_lookup.get((s.question_id, item_id, code_value), code_value.strip().lower() in MISSING_CODE_DEFAULTS)
                        choice_rows.append(
                            {
                                "respondent_id": respondent_id,
                                "question_id": s.question_id,
                                "item_id": item_id,
                                "code_id": code_lookup.get((s.question_id, item_id, code_value)),
                                "code_value": code_value,
                                "selected": True,
                                "weight": weight,
                                "compute_in_base": not is_missing and not s.ignored_for_compute,
                            }
                        )
                elif qtype in {"ranking", "constant_sum", "numeric"}:
                    num = pd.to_numeric(raw, errors="coerce")
                    if pd.isna(num):
                        continue
                    value_rows.append(
                        {
                            "respondent_id": respondent_id,
                            "question_id": s.question_id,
                            "item_id": item_id,
                            "numeric_value": float(num),
                            "weight": weight,
                            "compute_in_base": not s.ignored_for_compute,
                        }
                    )
                else:
                    # text/unknown: intentionally ignored from compute facts
                    continue

    return pd.DataFrame(choice_rows), pd.DataFrame(value_rows)


def _build_schema_registry(project_id: str, model_version: str, specs: list[QuestionSpec], banners: list[BannerSpec]) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "model_version": model_version,
        "questions": [
            {
                "id": s.question_id,
                "text": s.text,
                "type": s.qtype,
                "group": s.group,
                "ignored_for_compute": s.ignored_for_compute,
                "is_open_ended": s.is_open_ended,
                "items": [{"id": i.key, "text": i.text, "column": i.column} for i in s.items],
                "codes": [
                    {"value": c.value, "text": c.text, "is_missing": bool(c.is_missing) or str(c.value).strip().lower() in MISSING_CODE_DEFAULTS}
                    for c in s.codes
                ],
            }
            for s in specs
        ],
        "banners": [{"id": b.banner_id, "text": b.text, "column": b.column} for b in banners],
    }
