from fastapi import APIRouter

from app.models.schema import NetDefinition, Variable
from app.services.schema_inference import schema_inference_service

router = APIRouter()


@router.get("/variables", response_model=list[Variable])
def infer_variables() -> list[Variable]:
    return schema_inference_service.infer_variables()


@router.get("/nets", response_model=list[NetDefinition])
def infer_nets() -> list[NetDefinition]:
    return schema_inference_service.infer_nets()
