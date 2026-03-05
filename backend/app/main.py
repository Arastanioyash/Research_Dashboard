from fastapi import FastAPI

from .compute import compute_nps

app = FastAPI(title="Research Dashboard Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics/nps")
def sample_nps() -> dict[str, int]:
    metrics = compute_nps([10, 9, 8, 6, 5])
    return {
        "promoters": metrics.promoters,
        "passives": metrics.passives,
        "detractors": metrics.detractors,
        "nps": metrics.nps,
    }
