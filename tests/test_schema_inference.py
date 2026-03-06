from backend.app.analytics import infer_schema


def test_infer_schema_for_mixed_columns() -> None:
    rows = [
        {"respondent_id": "1", "score": "4", "is_complete": "true", "comment": "ok"},
        {"respondent_id": "2", "score": "4.5", "is_complete": "false", "comment": ""},
    ]

    schema = infer_schema(rows)

    assert schema == {
        "respondent_id": "integer",
        "score": "float",
        "is_complete": "boolean",
        "comment": "string",
    }
