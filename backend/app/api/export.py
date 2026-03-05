from fastapi import APIRouter

router = APIRouter()


@router.get("/csv")
def export_csv() -> dict[str, str]:
    return {"message": "CSV export placeholder"}
