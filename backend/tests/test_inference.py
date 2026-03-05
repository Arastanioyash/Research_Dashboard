from app.inference import infer_question_types


def test_inference_unknown_text_exclusions_and_major_types() -> None:
    columns = {
        "satisfaction_single_select": ["Good", "Bad", "Good"],
        "features_multi_select_binary": [1, 0, 1, 0],
        "service_grid_likert": [1, 3, 5, 4],
        "brand_nps": [0, 6, 7, 9, 10],
        "spend_constant_sum": [15, 40, 45],
        "age_numeric": [25, 34, 29],
        "open_text_feedback": ["great app", "needs dark mode"],
        "mystery_field": [
            "alpha",
            "beta",
            "gamma",
            "delta",
            "epsilon",
            "zeta",
            "eta",
            "theta",
            "iota",
        ],
    }

    result = infer_question_types(columns)

    assert result["satisfaction_single_select"].major_type == "choice"
    assert result["satisfaction_single_select"].subtype == "single_select"

    assert result["features_multi_select_binary"].subtype == "multi_select_binary"
    assert result["service_grid_likert"].subtype == "grid_likert"
    assert result["brand_nps"].subtype == "nps"
    assert result["spend_constant_sum"].subtype == "constant_sum"
    assert result["age_numeric"].subtype == "numeric"

    assert result["open_text_feedback"].major_type == "text"
    assert result["mystery_field"].major_type == "unknown"
