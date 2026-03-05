from app.compute import compute_nps


def test_compute_nps_pipeline() -> None:
    metrics = compute_nps([10, 10, 9, 8, 7, 6, 5, 4])

    assert metrics.promoters == 3
    assert metrics.passives == 2
    assert metrics.detractors == 3
    assert metrics.nps == 0
