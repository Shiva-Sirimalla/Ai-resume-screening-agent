import json
import os

from openai import OpenAI

_client = None

PROVIDERS = {
    "groq": {
        "keys": ("GROQ_API_KEY",),
        "base_url": "https://api.groq.com/openai/v1",
        "model_env": "GROQ_MODEL",
        "default_model": "llama-3.3-70b-versatile",
    },
    "grok": {
        "keys": ("GROK_API_KEY", "XAI_API_KEY"),
        "base_url": "https://api.x.ai/v1",
        "model_env": "GROK_MODEL",
        "default_model": "grok-3-mini",
    },
    "openai": {
        "keys": ("OPENAI_API_KEY",),
        "base_url": None,
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4.1-mini",
    },
}


def _find_key(provider):
    for name in PROVIDERS[provider]["keys"]:
        value = os.getenv(name)
        if value:
            return value
    return None


def _resolve_provider():
    forced = os.getenv("LLM_PROVIDER", "").lower().strip()
    if forced:
        if forced not in PROVIDERS:
            raise ValueError(f"Unknown LLM_PROVIDER: {forced}")
        if not _find_key(forced):
            raise ValueError(f"No API key set for LLM_PROVIDER={forced}")
        return forced
    for name in ("groq", "grok", "openai"):
        if _find_key(name):
            return name
    raise ValueError("No API key found in .env")


def _api_config():
    provider = _resolve_provider()
    cfg = PROVIDERS[provider]
    return {
        "provider": provider,
        "api_key": _find_key(provider),
        "base_url": cfg["base_url"],
        "model": os.getenv(cfg["model_env"], cfg["default_model"]),
    }


def _client_instance():
    global _client
    if _client is None:
        cfg = _api_config()
        kwargs = {"api_key": cfg["api_key"]}
        if cfg["base_url"]:
            kwargs["base_url"] = cfg["base_url"]
        _client = OpenAI(**kwargs)
    return _client


def _fallback(raw):
    return {
        "candidate_summary": raw,
        "matching_skills": [],
        "missing_skills": [],
        "recommendation": raw,
        "interview_questions": [],
        "fit_score": 50,
        "verdict": "Maybe",
    }


def ai_screening(resume_text, job_description):
    cfg = _api_config()
    prompt = f"""You are an expert AI HR recruiter.

Resume:
{resume_text[:6000]}

Job Description:
{job_description[:4000]}

Return JSON only with keys:
candidate_summary, matching_skills (array), missing_skills (array),
recommendation, interview_questions (array of 3 strings),
fit_score (0-100 integer), verdict (Hire|Maybe|Reject)"""

    try:
        resp = _client_instance().chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)
        data["fit_score"] = int(data.get("fit_score", 50))
        data["verdict"] = data.get("verdict", "Maybe")
        return data
    except Exception:
        resp = _client_instance().chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return _fallback(resp.choices[0].message.content)
