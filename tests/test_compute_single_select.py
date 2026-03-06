from backend.app.analytics import compute_single_select_mean


def test_compute_single_select_mean_ignores_unknown_values() -> None:
    responses = ["Very likely", "Likely", "Unknown", "Likely", ""]
    score_map = {"Very likely": 5, "Likely": 4, "Neutral": 3, "Unlikely": 2}

    mean = compute_single_select_mean(responses, score_map)

    assert mean == 13 / 3
