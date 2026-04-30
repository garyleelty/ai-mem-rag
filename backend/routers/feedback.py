import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.db_models import User, QARecord, Feedback
from models.schemas import FeedbackCreate, FeedbackUpdate, FeedbackResponse

router = APIRouter(prefix="/api/v1/qa/records", tags=["feedback"])


@router.post("/{record_id}/feedback", response_model=FeedbackResponse)
def create_feedback(
    record_id: int,
    body: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")

    existing = db.query(Feedback).filter(Feedback.qa_record_id == record_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already exists for this record")

    feedback = Feedback(
        qa_record_id=record_id,
        user_id=current_user.id,
        feedback_type=body.feedback_type,
        modified_answer=body.modified_answer,
        preset_tags=json.dumps(body.preset_tags) if body.preset_tags else None,
        custom_tags=json.dumps(body.custom_tags) if body.custom_tags else None,
        comment=body.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/{record_id}/feedback", response_model=FeedbackResponse)
def get_feedback(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")

    feedback = db.query(Feedback).filter(Feedback.qa_record_id == record_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback


@router.put("/{record_id}/feedback", response_model=FeedbackResponse)
def update_feedback(
    record_id: int,
    body: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")

    feedback = db.query(Feedback).filter(Feedback.qa_record_id == record_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    if body.feedback_type is not None:
        feedback.feedback_type = body.feedback_type
    if body.modified_answer is not None:
        feedback.modified_answer = body.modified_answer
    if body.preset_tags is not None:
        feedback.preset_tags = json.dumps(body.preset_tags)
    if body.custom_tags is not None:
        feedback.custom_tags = json.dumps(body.custom_tags)
    if body.comment is not None:
        feedback.comment = body.comment

    db.commit()
    db.refresh(feedback)
    return feedback


@router.delete("/{record_id}/feedback")
def delete_feedback(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")

    feedback = db.query(Feedback).filter(Feedback.qa_record_id == record_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    db.delete(feedback)
    db.commit()
    return {"message": "Feedback deleted"}
