from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb


class DuckDBService:
    """DuckDB query helper for Parquet-backed project model data."""

    def __init__(self, project_model_dir: str | Path):
        self.project_model_dir = Path(project_model_dir)

    def query_parquet(
        self,
        relative_glob: str,
        columns: list[str] | None = None,
        filters: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        parquet_glob = str(self.project_model_dir / relative_glob)
        projection = ", ".join(columns) if columns else "*"

        sql = f"SELECT {projection} FROM read_parquet('{parquet_glob}')"
        if filters:
            sql += f" WHERE {filters}"
        if limit is not None:
            sql += f" LIMIT {limit}"

        with duckdb.connect(database=":memory:") as conn:
            relation = conn.sql(sql)
            rows = relation.fetchall()
            col_names = [c[0] for c in relation.description]

        return [dict(zip(col_names, row, strict=False)) for row in rows]
