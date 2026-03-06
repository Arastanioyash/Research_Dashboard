from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.views import SavedViewCreate, SavedViewRead, SavedViewUpdate
from app.services.views_service import UserContext, ViewsService

router = APIRouter(prefix="/projects/{id}/views", tags=["views"])


# These dependencies are intentionally lightweight placeholders so this module
# can be integrated into an existing app wiring with minimal changes.
def get_db_session() -> Session:
    raise NotImplementedError("Wire get_db_session to your SQLAlchemy Session dependency")


def get_current_user() -> UserContext:
    raise NotImplementedError("Wire get_current_user to your auth dependency")


@router.post("", response_model=SavedViewRead, status_code=status.HTTP_201_CREATED)
def create_saved_view(
    id: int,
    payload: SavedViewCreate,
    db: Session = Depends(get_db_session),
    current_user: UserContext = Depends(get_current_user),
) -> SavedViewRead:
    service = ViewsService(db)
    entity = service.create_view(project_id=id, payload=payload, user=current_user)
    return SavedViewRead.model_validate(entity)


@router.get("", response_model=list[SavedViewRead])
def list_saved_views(
    id: int,
    db: Session = Depends(get_db_session),
    current_user: UserContext = Depends(get_current_user),
) -> list[SavedViewRead]:
    service = ViewsService(db)
    return [SavedViewRead.model_validate(item) for item in service.list_views(project_id=id, user=current_user)]


@router.get("/{view_id}", response_model=SavedViewRead)
def get_saved_view(
    id: int,
    view_id: int,
    db: Session = Depends(get_db_session),
    current_user: UserContext = Depends(get_current_user),
) -> SavedViewRead:
    service = ViewsService(db)
    entity = service.get_view(project_id=id, view_id=view_id, user=current_user)
    return SavedViewRead.model_validate(entity)


@router.patch("/{view_id}", response_model=SavedViewRead)
def update_saved_view(
    id: int,
    view_id: int,
    payload: SavedViewUpdate,
    db: Session = Depends(get_db_session),
    current_user: UserContext = Depends(get_current_user),
) -> SavedViewRead:
    service = ViewsService(db)
    entity = service.update_view(project_id=id, view_id=view_id, payload=payload, user=current_user)
    return SavedViewRead.model_validate(entity)


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_view(
    id: int,
    view_id: int,
    db: Session = Depends(get_db_session),
    current_user: UserContext = Depends(get_current_user),
) -> None:
    service = ViewsService(db)
    service.delete_view(project_id=id, view_id=view_id, user=current_user)

