import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.db_models import User, UserPreference
from models.schemas import PreferenceUpdate, PreferenceResponse

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


def _get_or_create_preference(db: Session, user_id: int) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.get("", response_model=PreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = _get_or_create_preference(db, current_user.id)
    return pref


@router.put("", response_model=PreferenceResponse)
def update_preferences(
    body: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = _get_or_create_preference(db, current_user.id)

    if body.preferred_style is not None:
        pref.preferred_style = body.preferred_style
    if body.preferred_language is not None:
        pref.preferred_language = body.preferred_language
    if body.domain_interests is not None:
        pref.domain_interests = json.dumps(body.domain_interests)
    if body.custom_prompt is not None:
        pref.custom_prompt = body.custom_prompt
    if body.auto_summary is not None:
        pref.auto_summary = body.auto_summary

    db.commit()
    db.refresh(pref)
    return pref
