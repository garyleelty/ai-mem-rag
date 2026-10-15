from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    qa_records = relationship("QARecord", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    preference = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String)
    source = Column(String, default="api")
    model_name = Column(String)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    qa_records = relationship("QARecord", back_populates="conversation", cascade="all, delete-orphan")


class QARecord(Base):
    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    model_name = Column(String)
    temperature = Column(Float)
    tokens_used = Column(Integer)
    latency_ms = Column(Integer)
    sequence_order = Column(Integer, default=0)
    chroma_doc_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="qa_records")
    conversation = relationship("Conversation", back_populates="qa_records")
    feedback = relationship("Feedback", back_populates="qa_record", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    qa_record_id = Column(Integer, ForeignKey("qa_records.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String, nullable=False)
    modified_answer = Column(Text)
    preset_tags = Column(Text)
    custom_tags = Column(Text)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    qa_record = relationship("QARecord", back_populates="feedback")
    user = relationship("User", back_populates="feedbacks")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    preferred_style = Column(String, default="balanced")
    preferred_language = Column(String, default="zh")
    domain_interests = Column(Text)
    custom_prompt = Column(Text)
    auto_summary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preference")


class PresetTag(Base):
    __tablename__ = "preset_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    color = Column(String, default="#3b82f6")
    category = Column(String, default="general")
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentIndex(Base):
    __tablename__ = "document_indices"

    id = Column(Integer, primary_key=True, index=True)
    chroma_doc_id = Column(String, unique=True, nullable=False, index=True)
    collection_name = Column(String, nullable=False, index=True)
    filename = Column(String)
    chunk_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
