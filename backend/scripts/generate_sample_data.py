#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def generate_sample_rows() -> list[dict[str, str]]:
    return [
        {
            "respondent_id": "1",
            "age_band": "25-34",
            "region": "North",
            "q_brand_awareness": "Aware",
            "q_purchase_intent": "Likely",
            "q_nps": "8",
            "q_channels": "Social|Email",
        },
        {
            "respondent_id": "2",
            "age_band": "35-44",
            "region": "South",
            "q_brand_awareness": "Not aware",
            "q_purchase_intent": "Neutral",
            "q_nps": "6",
            "q_channels": "TV|Retail",
        },
        {
            "respondent_id": "3",
            "age_band": "18-24",
            "region": "North",
            "q_brand_awareness": "Aware",
            "q_purchase_intent": "Very likely",
            "q_nps": "9",
            "q_channels": "Social|Influencer",
        },
    ]


def generate_metadata() -> dict:
    return {
        "survey_name": "Research Dashboard Demo",
        "questions": [
            {
                "id": "q_brand_awareness",
                "label": "Are you aware of the brand?",
                "type": "single_select",
                "options": ["Aware", "Not aware"],
            },
            {
                "id": "q_purchase_intent",
                "label": "How likely are you to purchase?",
                "type": "single_select",
                "options": ["Very likely", "Likely", "Neutral", "Unlikely"],
                "score_map": {
                    "Very likely": 5,
                    "Likely": 4,
                    "Neutral": 3,
                    "Unlikely": 2,
                },
            },
            {
                "id": "q_channels",
                "label": "Which channels influenced you?",
                "type": "multi_select",
                "separator": "|",
            },
        ],
    }


def generate_banner_metadata() -> dict:
    return {
        "banners": [
            {"field": "age_band", "label": "Age Band"},
            {"field": "region", "label": "Region"},
        ]
    }


def write_csv(rows: list[dict[str, str]], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(payload: dict, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sample data files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("backend/sample_data"),
        help="Directory to write generated files",
    )
    args = parser.parse_args()

    rows = generate_sample_rows()
    metadata = generate_metadata()
    banner_metadata = generate_banner_metadata()

    write_csv(rows, args.output_dir / "sample_responses_wide.csv")
    write_json(metadata, args.output_dir / "sample_metadata.json")
    write_json(banner_metadata, args.output_dir / "sample_banner_metadata.json")

    print(f"Sample files generated in {args.output_dir}")


if __name__ == "__main__":
    main()
