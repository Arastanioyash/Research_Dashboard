from fastapi import APIRouter

from app.services.compute_engine import compute_engine

router = APIRouter()


@router.get("/summary")
def get_summary() -> dict[str, str]:
    return compute_engine.summary()
