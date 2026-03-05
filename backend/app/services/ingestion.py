from pathlib import Path

import polars as pl


class IngestionService:
    def load_tabular(self, file_path: Path) -> pl.DataFrame:
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            return pl.read_csv(file_path)
        if suffix in {".xlsx", ".xls"}:
            return pl.read_excel(file_path)
        raise ValueError(f"Unsupported file type: {suffix}")


ingestion_service = IngestionService()
