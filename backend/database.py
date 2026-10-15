from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from config import SQLITE_PATH

engine = create_engine(f"sqlite:///{SQLITE_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models.db_models import User, Conversation, QARecord, Feedback, UserPreference, PresetTag, DocumentIndex
    Base.metadata.create_all(bind=engine)
    _create_indexes()
    _seed_preset_tags()


def _create_indexes():
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_qa_records_user_created ON qa_records(user_id, created_at DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_qa_records_conversation ON qa_records(conversation_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_feedbacks_qa_record ON feedbacks(qa_record_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_conversations_user_updated ON conversations(user_id, updated_at DESC)"))


def _seed_preset_tags():
    from models.db_models import PresetTag
    db = SessionLocal()
    try:
        existing = db.query(PresetTag).count()
        if existing > 0:
            return
        defaults = [
            PresetTag(name="accurate", label="准确", color="#22c55e", category="quality"),
            PresetTag(name="concise", label="简洁", color="#3b82f6", category="style"),
            PresetTag(name="detailed", label="详细", color="#8b5cf6", category="style"),
            PresetTag(name="helpful", label="有帮助", color="#22c55e", category="quality"),
            PresetTag(name="creative", label="有创意", color="#f59e0b", category="style"),
            PresetTag(name="outdated", label="过时", color="#ef4444", category="quality"),
            PresetTag(name="incorrect", label="不准确", color="#ef4444", category="quality"),
            PresetTag(name="easy_to_understand", label="易懂", color="#3b82f6", category="style"),
        ]
        db.add_all(defaults)
        db.commit()
    finally:
        db.close()
