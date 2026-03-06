from __future__ import annotations

import csv
import io
import logging
from collections import Counter

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.models import (
    BannerMetadataUploadRequest,
    BannerSpecModel,
    MetadataUploadRequest,
    Metric,
    NetDefinitionModel,
    PageQuestionMappingRequest,
    PageSpecModel,
    ResultResponse,
    SchemaResponse,
    SchemaUpdateRequest,
    TidyResultRow,
    UploadResponse,
)
from app.services.store import store

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger("research_dashboard")


def _refresh_project(project_id: str, reason: str) -> None:
    state = store.project(project_id)
    logger.info(
        "refresh_project",
        extra={
            "project_id": project_id,
            "reason": reason,
            "row_count": len(state.csv_rows),
            "schema_fields": len(state.schema),
        },
    )


def _apply_filters(rows: list[dict[str, str]], filters: str | None) -> list[dict[str, str]]:
    if not filters:
        return rows

    clauses: list[tuple[str, str]] = []
    for part in filters.split(","):
        if not part.strip():
            continue
        if ":" not in part:
            raise HTTPException(status_code=400, detail=f"Invalid filter clause: {part}")
        key, value = part.split(":", 1)
        clauses.append((key.strip(), value.strip()))

    filtered = rows
    for key, value in clauses:
        filtered = [row for row in filtered if row.get(key) == value]
    return filtered


def _compute_tidy_result(
    project_id: str,
    question_id: str,
    banner_id: str | None,
    filters: str | None,
    metric: Metric,
) -> ResultResponse:
    state = store.project(project_id)
    logger.info(
        "compute_result_start",
        extra={
            "project_id": project_id,
            "question_id": question_id,
            "banner_id": banner_id,
            "filters": filters,
            "metric": metric.value,
        },
    )

    rows = _apply_filters(state.csv_rows, filters)
    if not rows:
        logger.info("compute_result_complete", extra={"project_id": project_id, "rows": 0})
        return ResultResponse(project_id=project_id, metric=metric, rows=[])

    counter: Counter[tuple[str | None, str]] = Counter()
    for row in rows:
        answer = row.get(question_id)
        if answer is None:
            continue
        banner_value = row.get(banner_id) if banner_id else None
        counter[(banner_value, answer)] += 1

    total = sum(counter.values())
    tidy_rows: list[TidyResultRow] = []
    for (banner_value, answer), count in counter.items():
        value = float(count)
        if metric == Metric.percent:
            value = (count / total) * 100 if total else 0.0
        tidy_rows.append(
            TidyResultRow(
                question_id=question_id,
                answer=answer,
                banner_value=banner_value,
                value=round(value, 4),
            )
        )

    tidy_rows.sort(key=lambda item: ((item.banner_value or ""), item.answer))
    logger.info("compute_result_complete", extra={"project_id": project_id, "rows": len(tidy_rows)})
    return ResultResponse(project_id=project_id, metric=metric, rows=tidy_rows)


@router.post("/{project_id}/upload/csv", response_model=UploadResponse)
async def upload_csv(project_id: str, file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    state = store.project(project_id)
    state.csv_rows = [dict(row) for row in reader]
    _refresh_project(project_id, "csv_upload")
    return UploadResponse(project_id=project_id, message="CSV uploaded", row_count=len(state.csv_rows))


@router.post("/{project_id}/upload/metadata", response_model=UploadResponse)
def upload_metadata(project_id: str, payload: MetadataUploadRequest) -> UploadResponse:
    state = store.project(project_id)
    state.metadata = payload.metadata
    _refresh_project(project_id, "metadata_upload")
    return UploadResponse(project_id=project_id, message="Metadata uploaded")


@router.post("/{project_id}/upload/banner-metadata", response_model=UploadResponse)
def upload_banner_metadata(project_id: str, payload: BannerMetadataUploadRequest) -> UploadResponse:
    state = store.project(project_id)
    state.banner_metadata = payload.banner_metadata
    _refresh_project(project_id, "banner_metadata_upload")
    return UploadResponse(project_id=project_id, message="Banner metadata uploaded")


@router.get("/{project_id}/schema", response_model=SchemaResponse)
def get_schema(project_id: str) -> SchemaResponse:
    state = store.project(project_id)
    return SchemaResponse(project_id=project_id, fields=state.schema)


@router.put("/{project_id}/schema", response_model=SchemaResponse)
def update_schema(project_id: str, payload: SchemaUpdateRequest) -> SchemaResponse:
    state = store.project(project_id)
    state.schema = payload.fields
    _refresh_project(project_id, "schema_update")
    return SchemaResponse(project_id=project_id, fields=state.schema)


@router.get("/{project_id}/banner-specs", response_model=list[BannerSpecModel])
def list_banner_specs(project_id: str) -> list[BannerSpecModel]:
    return list(store.project(project_id).banner_specs.values())


@router.post("/{project_id}/banner-specs", response_model=BannerSpecModel)
def create_banner_spec(project_id: str, payload: BannerSpecModel) -> BannerSpecModel:
    state = store.project(project_id)
    state.banner_specs[payload.id] = payload
    return payload


@router.get("/{project_id}/banner-specs/{banner_spec_id}", response_model=BannerSpecModel)
def get_banner_spec(project_id: str, banner_spec_id: str) -> BannerSpecModel:
    spec = store.project(project_id).banner_specs.get(banner_spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Banner spec not found")
    return spec


@router.put("/{project_id}/banner-specs/{banner_spec_id}", response_model=BannerSpecModel)
def update_banner_spec(project_id: str, banner_spec_id: str, payload: BannerSpecModel) -> BannerSpecModel:
    if payload.id != banner_spec_id:
        raise HTTPException(status_code=400, detail="Path id and payload id must match")
    store.project(project_id).banner_specs[banner_spec_id] = payload
    return payload


@router.delete("/{project_id}/banner-specs/{banner_spec_id}", status_code=204)
def delete_banner_spec(project_id: str, banner_spec_id: str) -> None:
    store.project(project_id).banner_specs.pop(banner_spec_id, None)


@router.get("/{project_id}/net-definitions", response_model=list[NetDefinitionModel])
def list_net_definitions(project_id: str) -> list[NetDefinitionModel]:
    return list(store.project(project_id).net_definitions.values())


@router.post("/{project_id}/net-definitions", response_model=NetDefinitionModel)
def create_net_definition(project_id: str, payload: NetDefinitionModel) -> NetDefinitionModel:
    state = store.project(project_id)
    state.net_definitions[payload.id] = payload
    return payload


@router.get("/{project_id}/net-definitions/{net_id}", response_model=NetDefinitionModel)
def get_net_definition(project_id: str, net_id: str) -> NetDefinitionModel:
    net = store.project(project_id).net_definitions.get(net_id)
    if not net:
        raise HTTPException(status_code=404, detail="Net definition not found")
    return net


@router.put("/{project_id}/net-definitions/{net_id}", response_model=NetDefinitionModel)
def update_net_definition(project_id: str, net_id: str, payload: NetDefinitionModel) -> NetDefinitionModel:
    if payload.id != net_id:
        raise HTTPException(status_code=400, detail="Path id and payload id must match")
    store.project(project_id).net_definitions[net_id] = payload
    return payload


@router.delete("/{project_id}/net-definitions/{net_id}", status_code=204)
def delete_net_definition(project_id: str, net_id: str) -> None:
    store.project(project_id).net_definitions.pop(net_id, None)


@router.get("/{project_id}/page-specs", response_model=list[PageSpecModel])
def list_page_specs(project_id: str) -> list[PageSpecModel]:
    return list(store.project(project_id).page_specs.values())


@router.post("/{project_id}/page-specs", response_model=PageSpecModel)
def create_page_spec(project_id: str, payload: PageSpecModel) -> PageSpecModel:
    store.project(project_id).page_specs[payload.id] = payload
    return payload


@router.get("/{project_id}/page-specs/{page_id}", response_model=PageSpecModel)
def get_page_spec(project_id: str, page_id: str) -> PageSpecModel:
    page = store.project(project_id).page_specs.get(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page spec not found")
    return page


@router.put("/{project_id}/page-specs/{page_id}", response_model=PageSpecModel)
def update_page_spec(project_id: str, page_id: str, payload: PageSpecModel) -> PageSpecModel:
    if payload.id != page_id:
        raise HTTPException(status_code=400, detail="Path id and payload id must match")
    store.project(project_id).page_specs[page_id] = payload
    return payload


@router.delete("/{project_id}/page-specs/{page_id}", status_code=204)
def delete_page_spec(project_id: str, page_id: str) -> None:
    state = store.project(project_id)
    state.page_specs.pop(page_id, None)
    state.page_questions.pop(page_id, None)


@router.get("/{project_id}/page-specs/{page_id}/questions", response_model=PageQuestionMappingRequest)
def get_page_questions(project_id: str, page_id: str) -> PageQuestionMappingRequest:
    state = store.project(project_id)
    return PageQuestionMappingRequest(question_ids=state.page_questions.get(page_id, []))


@router.put("/{project_id}/page-specs/{page_id}/questions", response_model=PageQuestionMappingRequest)
def upsert_page_questions(
    project_id: str,
    page_id: str,
    payload: PageQuestionMappingRequest,
) -> PageQuestionMappingRequest:
    state = store.project(project_id)
    state.page_questions[page_id] = payload.question_ids
    return payload


@router.get("/{project_id}/result", response_model=ResultResponse)
def get_project_result(
    project_id: str,
    question_id: str = Query(..., min_length=1),
    banner_id: str | None = None,
    filters: str | None = None,
    metric: Metric = Metric.count,
) -> ResultResponse:
    return _compute_tidy_result(project_id, question_id, banner_id, filters, metric)


@router.get("/{project_id}/export")
def export_project_result(
    project_id: str,
    question_id: str = Query(..., min_length=1),
    banner_id: str | None = None,
    filters: str | None = None,
    metric: Metric = Metric.count,
) -> StreamingResponse:
    result = _compute_tidy_result(project_id, question_id, banner_id, filters, metric)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["question_id", "answer", "banner_value", "value"])
    for row in result.rows:
        writer.writerow([row.question_id, row.answer, row.banner_value or "", row.value])
    output.seek(0)

    filename = f"project_{project_id}_result.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
