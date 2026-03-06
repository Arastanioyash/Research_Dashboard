from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.projects import router as projects_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="Research Dashboard API")
app.include_router(projects_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
