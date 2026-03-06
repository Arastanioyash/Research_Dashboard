import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from research_dashboard.compute_engine import CacheConfig, ComputeEngine


class ComputeEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.fact_path = str(base / "fact.parquet")
        self.dim_path = str(base / "dim.parquet")
        self.cache_path = str(base / "tabulation_cache.parquet")

        con = duckdb.connect()
        con.execute(
            """
            COPY (
                SELECT * FROM (
                    VALUES
                    ('r1','Q1','A',NULL,NULL,1,8, NULL, 'US'),
                    ('r2','Q1','B',NULL,NULL,1,6, NULL, 'US'),
                    ('r3','Q1','A',NULL,NULL,2,10,NULL, 'UK'),
                    ('r1','Q2',NULL,'feature_1',1,1,NULL,1.0,'US'),
                    ('r2','Q2',NULL,'feature_2',2,1,NULL,2.0,'US'),
                    ('r3','Q2',NULL,'feature_1',1,2,NULL,3.0,'UK')
                ) AS t(respondent_id, question_id, answer_code, grid_row, grid_col, rank_value, numeric_value, weight, country)
            ) TO ? (FORMAT PARQUET)
            """,
            [self.fact_path],
        )
        con.execute(
            """
            COPY (
                SELECT * FROM (
                    VALUES
                    ('r1','18-24','M'),
                    ('r2','25-34','F'),
                    ('r3','25-34','M')
                ) AS t(respondent_id, age_band, gender)
            ) TO ? (FORMAT PARQUET)
            """,
            [self.dim_path],
        )

        self.engine = ComputeEngine(
            fact_parquet_path=self.fact_path,
            respondent_parquet_path=self.dim_path,
            cache=CacheConfig(mode="parquet", parquet_path=self.cache_path),
            banner_specs={"age": {"field": "age_band"}},
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_filter_hash_stable(self) -> None:
        a = [{"field": "country", "op": "in", "value": ["US", "UK"]}]
        b = [{"op": "in", "value": ["UK", "US"], "field": "country"}]
        self.assertEqual(self.engine.filter_hash(a), self.engine.filter_hash(b))

    def test_single_select_with_filter_and_banner(self) -> None:
        payload = self.engine.compute_single_select(
            question_id="Q1",
            filter_chips_json=json.dumps([{"field": "country", "op": "eq", "value": "US"}]),
            banner_id="age",
        )
        self.assertEqual(payload["metric"]["name"], "single_select")
        self.assertEqual(len(payload["rows"]), 2)

    def test_cache_written_and_read(self) -> None:
        p1 = self.engine.compute_numeric(question_id="Q1")
        p2 = self.engine.compute_numeric(question_id="Q1")
        self.assertEqual(p1, p2)
        self.assertTrue(Path(self.cache_path).exists())


if __name__ == "__main__":
    unittest.main()
