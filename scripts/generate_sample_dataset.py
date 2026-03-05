#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path


OUTPUT = Path("data/sample_survey.csv")


ROWS = [
    {
        "single_select": "Product A",
        "multi_feature_chatbot": 1,
        "multi_feature_reports": 0,
        "grid_likert_usability": 5,
        "grid_likert_speed": 4,
        "nps": 10,
        "ranking_price": 1,
        "ranking_quality": 2,
        "constant_sum_ads": 30,
        "constant_sum_research": 70,
        "numeric_age": 29,
        "text_feedback": "Great experience overall",
        "unknown_code": "XZ-100",
    },
    {
        "single_select": "Product B",
        "multi_feature_chatbot": 0,
        "multi_feature_reports": 1,
        "grid_likert_usability": 3,
        "grid_likert_speed": 2,
        "nps": 6,
        "ranking_price": 2,
        "ranking_quality": 1,
        "constant_sum_ads": 50,
        "constant_sum_research": 50,
        "numeric_age": 41,
        "text_feedback": "Needs better export options",
        "unknown_code": "QF-204",
    },
    {
        "single_select": "Product C",
        "multi_feature_chatbot": 1,
        "multi_feature_reports": 1,
        "grid_likert_usability": 4,
        "grid_likert_speed": 5,
        "nps": 8,
        "ranking_price": 3,
        "ranking_quality": 1,
        "constant_sum_ads": 20,
        "constant_sum_research": 80,
        "numeric_age": 35,
        "text_feedback": "I use it daily",
        "unknown_code": "MN-889",
    },
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(ROWS[0].keys())
    with OUTPUT.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ROWS)

    print(f"Wrote sample dataset to {OUTPUT}")


if __name__ == "__main__":
    main()
