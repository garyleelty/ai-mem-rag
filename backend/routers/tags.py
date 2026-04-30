from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.db_models import User, PresetTag
from models.schemas import PresetTagResponse, PresetTagCreate

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get("/preset", response_model=list[PresetTagResponse])
def list_preset_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(PresetTag).order_by(PresetTag.category, PresetTag.label).all()


@router.post("/preset", response_model=PresetTagResponse)
def create_preset_tag(
    body: PresetTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(PresetTag).filter(PresetTag.name == body.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag name already exists")

    tag = PresetTag(
        name=body.name,
        label=body.label,
        color=body.color or "#3b82f6",
        category=body.category or "general",
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
