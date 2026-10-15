from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, EMBEDDING_DEVICE

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    return _model


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts).tolist()


def warmup():
    model = get_embedding_model()
    model.encode(["warmup"])
