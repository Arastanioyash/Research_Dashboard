from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import duckdb


@dataclass(frozen=True)
class CacheConfig:
    mode: str = "parquet"  # parquet | duckdb
    parquet_path: str = "tabulation_cache.parquet"
    table_name: str = "tabulation_cache"


class ComputeEngine:
    def __init__(
        self,
        fact_parquet_path: str,
        respondent_parquet_path: str | None = None,
        conn_path: str = ":memory:",
        cache: CacheConfig | None = None,
        weight_column: str | None = "weight",
        banner_specs: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.conn = duckdb.connect(conn_path)
        self.fact_parquet_path = fact_parquet_path
        self.respondent_parquet_path = respondent_parquet_path
        self.cache = cache or CacheConfig()
        self.weight_column = weight_column
        self.banner_specs = banner_specs or {}

        self.conn.execute("CREATE OR REPLACE VIEW fact_responses AS SELECT * FROM read_parquet(?)", [fact_parquet_path])
        if respondent_parquet_path:
            self.conn.execute(
                "CREATE OR REPLACE VIEW dim_respondent AS SELECT * FROM read_parquet(?)",
                [respondent_parquet_path],
            )
        self._ensure_cache_store()

    @staticmethod
    def normalize_filter_state(filter_state: Any) -> Any:
        if isinstance(filter_state, dict):
            return {k: ComputeEngine.normalize_filter_state(filter_state[k]) for k in sorted(filter_state)}
        if isinstance(filter_state, list):
            normalized = [ComputeEngine.normalize_filter_state(item) for item in filter_state]
            try:
                return sorted(normalized, key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
            except TypeError:
                return normalized
        return filter_state

    @classmethod
    def filter_hash(cls, filter_state: Any) -> str:
        normalized = cls.normalize_filter_state(filter_state)
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _ensure_cache_store(self) -> None:
        self.conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.cache.table_name} (
                cache_key VARCHAR PRIMARY KEY,
                filter_hash VARCHAR,
                payload_json VARCHAR,
                updated_at TIMESTAMP
            )
            """
        )
        if self.cache.mode == "parquet":
            cache_path = Path(self.cache.parquet_path)
            if cache_path.exists():
                self.conn.execute(
                    f"INSERT OR REPLACE INTO {self.cache.table_name} SELECT * FROM read_parquet(?)",
                    [str(cache_path)],
                )

    def _flush_parquet_cache(self) -> None:
        if self.cache.mode != "parquet":
            return
        self.conn.execute(
            f"COPY (SELECT * FROM {self.cache.table_name}) TO ? (FORMAT PARQUET)",
            [self.cache.parquet_path],
        )

    @staticmethod
    def _validate_identifier(identifier: str) -> str:
        if not identifier or not identifier.replace("_", "").isalnum():
            raise ValueError(f"Unsafe identifier: {identifier}")
        return identifier

    def _parse_filter_chips(self, filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None) -> tuple[str, list[Any]]:
        if not filter_chips_json:
            return "", []

        if isinstance(filter_chips_json, str):
            chips = json.loads(filter_chips_json)
        elif isinstance(filter_chips_json, dict):
            chips = filter_chips_json.get("chips", [])
        else:
            chips = filter_chips_json

        predicates: list[str] = []
        params: list[Any] = []

        for chip in chips:
            field = self._validate_identifier(chip["field"])
            op = chip.get("op", "eq").lower()
            value = chip.get("value")
            values = chip.get("values")
            qualified = f"f.{field}"

            if op == "eq":
                predicates.append(f"{qualified} = ?")
                params.append(value)
            elif op == "neq":
                predicates.append(f"{qualified} != ?")
                params.append(value)
            elif op == "in":
                vals = values if values is not None else value
                vals = vals if isinstance(vals, list) else [vals]
                placeholders = ",".join(["?"] * len(vals))
                predicates.append(f"{qualified} IN ({placeholders})")
                params.extend(vals)
            elif op == "not_in":
                vals = values if values is not None else value
                vals = vals if isinstance(vals, list) else [vals]
                placeholders = ",".join(["?"] * len(vals))
                predicates.append(f"{qualified} NOT IN ({placeholders})")
                params.extend(vals)
            elif op == "gt":
                predicates.append(f"{qualified} > ?")
                params.append(value)
            elif op == "gte":
                predicates.append(f"{qualified} >= ?")
                params.append(value)
            elif op == "lt":
                predicates.append(f"{qualified} < ?")
                params.append(value)
            elif op == "lte":
                predicates.append(f"{qualified} <= ?")
                params.append(value)
            elif op == "contains":
                predicates.append(f"CAST({qualified} AS VARCHAR) ILIKE ?")
                params.append(f"%{value}%")
            elif op == "between":
                lo, hi = value
                predicates.append(f"{qualified} BETWEEN ? AND ?")
                params.extend([lo, hi])
            elif op == "is_null":
                predicates.append(f"{qualified} IS NULL")
            elif op == "is_not_null":
                predicates.append(f"{qualified} IS NOT NULL")
            else:
                raise ValueError(f"Unsupported filter op: {op}")

        if not predicates:
            return "", []
        return "WHERE " + " AND ".join(predicates), params

    def _banner_slice_sql(self, banner_id: str | None) -> tuple[str, str, str]:
        if not banner_id:
            return "", "'All' AS banner_value", "banner_value"
        if not self.respondent_parquet_path:
            raise ValueError("banner_id was provided but dim_respondent parquet is not configured")

        spec = self.banner_specs.get(banner_id)
        if not spec:
            raise ValueError(f"Unknown banner_id: {banner_id}")

        fields = spec.get("fields") or ([spec["field"]] if "field" in spec else [])
        if not fields:
            raise ValueError(f"Banner spec for {banner_id} must provide field or fields")

        safe_fields = [self._validate_identifier(x) for x in fields]
        if len(safe_fields) == 1:
            expr = f"d.{safe_fields[0]}"
        else:
            expr = " || ' | ' || ".join([f"COALESCE(CAST(d.{f} AS VARCHAR), 'Unknown')" for f in safe_fields])

        join_sql = "LEFT JOIN dim_respondent d ON f.respondent_id = d.respondent_id"
        return join_sql, f"{expr} AS banner_value", "banner_value"

    def _cache_get(self, cache_key: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            f"SELECT payload_json FROM {self.cache.table_name} WHERE cache_key = ?",
            [cache_key],
        ).fetchone()
        return json.loads(row[0]) if row else None

    def _cache_set(self, cache_key: str, filter_hash: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            f"""
            INSERT OR REPLACE INTO {self.cache.table_name} (cache_key, filter_hash, payload_json, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            [cache_key, filter_hash, json.dumps(payload, separators=(",", ":")), datetime.now(timezone.utc)],
        )
        self._flush_parquet_cache()

    def _compute_rows(
        self,
        sql: str,
        params: Iterable[Any],
        *,
        weighted: bool,
        metric: str,
        dimensions: list[str],
        cache_key: str,
        filter_hash: str,
    ) -> dict[str, Any]:
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        rows = [dict(zip([c[0] for c in self.conn.description], row)) for row in self.conn.execute(sql, list(params)).fetchall()]
        payload = {
            "rows": rows,
            "weighted": weighted,
            "metric": {
                "name": metric,
                "dimensions": dimensions,
            },
            "filter_hash": filter_hash,
        }
        self._cache_set(cache_key, filter_hash, payload)
        return payload

    def compute_single_select(
        self,
        *,
        question_id: str,
        answer_column: str = "answer_code",
        filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        banner_id: str | None = None,
    ) -> dict[str, Any]:
        answer_column = self._validate_identifier(answer_column)
        where_sql, params = self._parse_filter_chips(filter_chips_json)
        join_sql, banner_expr, banner_group = self._banner_slice_sql(banner_id)
        f_hash = self.filter_hash(filter_chips_json or [])
        cache_key = f"single_select:{question_id}:{answer_column}:{banner_id}:{f_hash}"
        weight_expr = f"COALESCE(f.{self.weight_column}, 1)" if self.weight_column else "1"

        sql = f"""
            SELECT
                {banner_expr},
                f.{answer_column} AS value,
                COUNT(*)::DOUBLE AS base_n,
                SUM({weight_expr})::DOUBLE AS weighted_n
            FROM fact_responses f
            {join_sql}
            {where_sql} {'AND' if where_sql else 'WHERE'} f.question_id = ?
            GROUP BY {banner_group}, f.{answer_column}
            ORDER BY {banner_group}, value
        """
        return self._compute_rows(sql, [*params, question_id], weighted=bool(self.weight_column), metric="single_select", dimensions=[banner_group, "value"], cache_key=cache_key, filter_hash=f_hash)

    def compute_multi_select(self, **kwargs: Any) -> dict[str, Any]:
        result = self.compute_single_select(**kwargs)
        result["metric"]["name"] = "multi_select"
        return result

    def compute_grid(
        self,
        *,
        question_id: str,
        row_column: str = "grid_row",
        col_column: str = "grid_col",
        filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        banner_id: str | None = None,
    ) -> dict[str, Any]:
        row_column = self._validate_identifier(row_column)
        col_column = self._validate_identifier(col_column)
        where_sql, params = self._parse_filter_chips(filter_chips_json)
        join_sql, banner_expr, banner_group = self._banner_slice_sql(banner_id)
        f_hash = self.filter_hash(filter_chips_json or [])
        cache_key = f"grid:{question_id}:{row_column}:{col_column}:{banner_id}:{f_hash}"

        sql = f"""
            SELECT
                {banner_expr},
                f.{row_column} AS row_key,
                f.{col_column} AS value,
                COUNT(*)::DOUBLE AS base_n
            FROM fact_responses f
            {join_sql}
            {where_sql} {'AND' if where_sql else 'WHERE'} f.question_id = ?
            GROUP BY {banner_group}, f.{row_column}, f.{col_column}
            ORDER BY {banner_group}, row_key, value
        """
        return self._compute_rows(sql, [*params, question_id], weighted=False, metric="grid", dimensions=[banner_group, "row_key", "value"], cache_key=cache_key, filter_hash=f_hash)

    def compute_nps(
        self,
        *,
        question_id: str,
        score_column: str = "numeric_value",
        filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        banner_id: str | None = None,
    ) -> dict[str, Any]:
        score_column = self._validate_identifier(score_column)
        where_sql, params = self._parse_filter_chips(filter_chips_json)
        join_sql, banner_expr, banner_group = self._banner_slice_sql(banner_id)
        f_hash = self.filter_hash(filter_chips_json or [])
        cache_key = f"nps:{question_id}:{score_column}:{banner_id}:{f_hash}"

        sql = f"""
            SELECT
                {banner_expr},
                'nps' AS value,
                COUNT(*)::DOUBLE AS base_n,
                (
                    100.0 * SUM(CASE WHEN f.{score_column} >= 9 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)
                    - 100.0 * SUM(CASE WHEN f.{score_column} <= 6 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)
                )::DOUBLE AS score
            FROM fact_responses f
            {join_sql}
            {where_sql} {'AND' if where_sql else 'WHERE'} f.question_id = ?
            GROUP BY {banner_group}
            ORDER BY {banner_group}
        """
        return self._compute_rows(sql, [*params, question_id], weighted=False, metric="nps", dimensions=[banner_group, "value"], cache_key=cache_key, filter_hash=f_hash)

    def compute_ranking(
        self,
        *,
        question_id: str,
        item_column: str = "answer_code",
        rank_column: str = "rank_value",
        filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        banner_id: str | None = None,
    ) -> dict[str, Any]:
        item_column = self._validate_identifier(item_column)
        rank_column = self._validate_identifier(rank_column)
        where_sql, params = self._parse_filter_chips(filter_chips_json)
        join_sql, banner_expr, banner_group = self._banner_slice_sql(banner_id)
        f_hash = self.filter_hash(filter_chips_json or [])
        cache_key = f"ranking:{question_id}:{item_column}:{rank_column}:{banner_id}:{f_hash}"

        sql = f"""
            SELECT
                {banner_expr},
                f.{item_column} AS value,
                COUNT(*)::DOUBLE AS base_n,
                AVG(f.{rank_column})::DOUBLE AS avg_rank
            FROM fact_responses f
            {join_sql}
            {where_sql} {'AND' if where_sql else 'WHERE'} f.question_id = ?
            GROUP BY {banner_group}, f.{item_column}
            ORDER BY {banner_group}, avg_rank ASC
        """
        return self._compute_rows(sql, [*params, question_id], weighted=False, metric="ranking", dimensions=[banner_group, "value"], cache_key=cache_key, filter_hash=f_hash)

    def compute_constant_sum(
        self,
        *,
        question_id: str,
        item_column: str = "answer_code",
        points_column: str = "numeric_value",
        filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        banner_id: str | None = None,
    ) -> dict[str, Any]:
        item_column = self._validate_identifier(item_column)
        points_column = self._validate_identifier(points_column)
        where_sql, params = self._parse_filter_chips(filter_chips_json)
        join_sql, banner_expr, banner_group = self._banner_slice_sql(banner_id)
        f_hash = self.filter_hash(filter_chips_json or [])
        cache_key = f"constant_sum:{question_id}:{item_column}:{points_column}:{banner_id}:{f_hash}"

        sql = f"""
            SELECT
                {banner_expr},
                f.{item_column} AS value,
                COUNT(*)::DOUBLE AS base_n,
                AVG(f.{points_column})::DOUBLE AS mean_points,
                SUM(f.{points_column})::DOUBLE AS total_points
            FROM fact_responses f
            {join_sql}
            {where_sql} {'AND' if where_sql else 'WHERE'} f.question_id = ?
            GROUP BY {banner_group}, f.{item_column}
            ORDER BY {banner_group}, value
        """
        return self._compute_rows(sql, [*params, question_id], weighted=False, metric="constant_sum", dimensions=[banner_group, "value"], cache_key=cache_key, filter_hash=f_hash)

    def compute_numeric(
        self,
        *,
        question_id: str,
        value_column: str = "numeric_value",
        filter_chips_json: str | dict[str, Any] | list[dict[str, Any]] | None = None,
        banner_id: str | None = None,
    ) -> dict[str, Any]:
        value_column = self._validate_identifier(value_column)
        where_sql, params = self._parse_filter_chips(filter_chips_json)
        join_sql, banner_expr, banner_group = self._banner_slice_sql(banner_id)
        f_hash = self.filter_hash(filter_chips_json or [])
        cache_key = f"numeric:{question_id}:{value_column}:{banner_id}:{f_hash}"

        sql = f"""
            SELECT
                {banner_expr},
                'numeric' AS value,
                COUNT(*)::DOUBLE AS base_n,
                AVG(f.{value_column})::DOUBLE AS mean,
                STDDEV_SAMP(f.{value_column})::DOUBLE AS std_dev,
                MIN(f.{value_column})::DOUBLE AS min,
                MAX(f.{value_column})::DOUBLE AS max
            FROM fact_responses f
            {join_sql}
            {where_sql} {'AND' if where_sql else 'WHERE'} f.question_id = ?
            GROUP BY {banner_group}
            ORDER BY {banner_group}
        """
        return self._compute_rows(sql, [*params, question_id], weighted=False, metric="numeric", dimensions=[banner_group, "value"], cache_key=cache_key, filter_hash=f_hash)
