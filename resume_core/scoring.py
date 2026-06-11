import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def create_embedding(text):
    return get_embedding_model().encode(text)


def create_embeddings(texts):
    return get_embedding_model().encode(texts)


def batch_semantic_scores(resume_embeddings, jd_embedding):
    resumes = np.atleast_2d(np.asarray(resume_embeddings, dtype=np.float32))
    if resumes.shape[0] == 0:
        return []

    jd = np.atleast_2d(np.asarray(jd_embedding, dtype=np.float32))
    faiss.normalize_L2(resumes)
    faiss.normalize_L2(jd)

    if resumes.shape[0] == 1:
        score = float(np.dot(resumes[0], jd[0]))
        return [round(score * 100, 2)]

    dim = resumes.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(resumes)
    scores, _ = index.search(jd, resumes.shape[0])
    return [round(float(s) * 100, 2) for s in scores[0]]


def composite_score(semantic_score, skill_score, ai_fit_score, weights):
    total = sum(weights.values())
    if total == 0:
        return 0.0
    score = (
        semantic_score * weights["semantic"]
        + skill_score * weights["skills"]
        + ai_fit_score * weights["ai"]
    ) / total
    return round(score, 2)


def score_tier(score):
    if score >= 75:
        return "Strong Match"
    if score >= 50:
        return "Moderate Match"
    return "Weak Match"
