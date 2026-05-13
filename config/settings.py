from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 向量数据库配置
    VECTOR_STORE_TYPE: str = "chroma"  # chroma | pinecone
    CHROMA_PATH: str = "./chroma_db"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENV: Optional[str] = None
    PINECONE_INDEX: str = "ai-memory-rag"
    
    # 关系数据库配置
    RELATIONAL_STORE_TYPE: str = "sqlite"  # sqlite | postgresql
    DATABASE_URL: str = "sqlite:///./ai-memory-rag.db"
    
    # Embedding 配置
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Streamlit 配置
    UI_HOST: str = "0.0.0.0"
    UI_PORT: int = 8501
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
