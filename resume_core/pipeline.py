from io import BytesIO
from pathlib import Path

from agents.screening_agent import ai_screening
from parser.docx_parser import extract_docx_text
from parser.pdf_parser import extract_pdf_text
from resume_core.scoring import (
    batch_semantic_scores,
    composite_score,
    create_embedding,
    create_embeddings,
)

SKILLS_DB = [
    "python", "java", "javascript", "typescript", "react", "node.js", "sql",
    "machine learning", "deep learning", "nlp", "genai", "llm", "rag",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd",
    "power bi", "tableau", "fastapi", "flask", "django",
    "streamlit", "langchain", "crewai", "git", "agile", "rest api",
    "mongodb", "postgresql", "redis", "spark", "hadoop",
]


def extract_skills(text):
    text = text.lower()
    return sorted({s for s in SKILLS_DB if s in text})


def skill_overlap_score(resume_skills, jd_skills):
    if not jd_skills:
        return 0.0
    matched = set(resume_skills) & set(jd_skills)
    return round(len(matched) / len(jd_skills) * 100, 2)


def skill_gap(resume_skills, jd_skills):
    return {
        "matched": sorted(set(resume_skills) & set(jd_skills)),
        "missing": sorted(set(jd_skills) - set(resume_skills)),
        "extra": sorted(set(resume_skills) - set(jd_skills)),
    }


class _LocalFile:
    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.name

    def seek(self, _pos=0):
        return None

    def read(self):
        return self.path.read_bytes()


def extract_resume_text(file):
    if isinstance(file, (str, Path)):
        file = _LocalFile(file)
    file.seek(0)
    name = file.name.lower()
    if name.endswith(".pdf"):
        if isinstance(file, _LocalFile):
            return extract_pdf_text(open(file.path, "rb"))
        return extract_pdf_text(file)
    if name.endswith(".docx"):
        data = file.path.read_bytes() if isinstance(file, _LocalFile) else file.read()
        return extract_docx_text(BytesIO(data))
    return ""


def run_screening_from_paths(resume_paths, job_description, weights, progress_callback=None):
    files = [_LocalFile(p) for p in resume_paths]
    return run_screening(files, job_description, weights, progress_callback)


def run_screening(uploaded_files, job_description, weights, progress_callback=None):
    jd_skills = extract_skills(job_description)
    jd_embedding = create_embedding(job_description)

    parsed = []
    for file in uploaded_files:
        text = extract_resume_text(file)
        if text.strip():
            parsed.append({"file": file, "text": text})

    if not parsed:
        return []

    resume_embeddings = create_embeddings([item["text"] for item in parsed])
    semantic_scores = batch_semantic_scores(resume_embeddings, jd_embedding)

    results = []
    total = len(parsed)

    for index, item in enumerate(parsed):
        file = item["file"]
        resume_text = item["text"]
        semantic_score = semantic_scores[index]

        if progress_callback:
            progress_callback(index, total, file.name, "Extracting skills")

        resume_skills = extract_skills(resume_text)
        skills_score = skill_overlap_score(resume_skills, jd_skills)
        gaps = skill_gap(resume_skills, jd_skills)

        if progress_callback:
            progress_callback(index, total, file.name, "Running AI analysis")

        analysis = ai_screening(resume_text, job_description)
        ai_fit = analysis.get("fit_score", 50)
        final_score = composite_score(semantic_score, skills_score, ai_fit, weights)

        ai_skills = analysis.get("matching_skills", [])
        all_matched = sorted(set(gaps["matched"]) | set(ai_skills))

        results.append({
            "Candidate": file.name,
            "Skills": ", ".join(resume_skills) if resume_skills else "None detected",
            "JD Skills": ", ".join(jd_skills) if jd_skills else "None detected",
            "Matched Skills": ", ".join(all_matched) if all_matched else "None",
            "Missing Skills": ", ".join(gaps["missing"]) if gaps["missing"] else "None",
            "Semantic Score": semantic_score,
            "Skills Score": skills_score,
            "AI Fit Score": ai_fit,
            "Composite Score": final_score,
            "Verdict": analysis.get("verdict", "Maybe"),
            "Summary": analysis.get("candidate_summary", ""),
            "Recommendation": analysis.get("recommendation", ""),
            "Interview Questions": analysis.get("interview_questions", []),
            "Analysis": analysis,
        })

        if progress_callback:
            progress_callback(index + 1, total, file.name, "Done")

    return results
