#!/usr/bin/env python3
"""
Resume Screening Agent — pure Python entry point.

  python main.py          Start the web UI
  python main.py check    Verify install and API key
  python main.py screen   Screen resumes from the command line
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _clear_cache():
    for folder in ROOT.rglob("__pycache__"):
        shutil.rmtree(folder, ignore_errors=True)


def _ensure_path():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def cmd_serve():
    _clear_cache()
    _ensure_path()
    app = ROOT / "app.py"
    print("Starting Resume Screening Agent at http://localhost:8501")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app), "--server.runOnSave", "true"],
        cwd=ROOT,
    )


def cmd_check():
    _ensure_path()
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    print("Python:", sys.version.split()[0])
    print("Project:", ROOT)

    missing = []
    for pkg in (
        "streamlit", "pandas", "numpy", "sklearn", "sentence_transformers",
        "faiss", "pdfplumber", "docx", "openai", "dotenv",
    ):
        try:
            __import__(pkg if pkg != "sklearn" else "sklearn")
            print(f"  OK  {pkg}")
        except ImportError:
            print(f"  MISSING  {pkg}")
            missing.append(pkg)

    import os

    has_key = bool(
        os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
        or os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    )
    if has_key:
        provider = os.getenv("LLM_PROVIDER") or (
            "groq" if os.getenv("GROQ_API_KEY") else
            "grok" if os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY") else
            "openai"
        )
        print(f"  OK  API key ({provider})")
    else:
        print("  WARN  No API key — add GROQ_API_KEY to .env")

    if missing:
        print("\nRun: python setup_env.py")
        sys.exit(1)
    print("\nAll checks passed. Run: python main.py")


def cmd_screen(args):
    _ensure_path()
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")

    import os

    if not any(os.getenv(k) for k in ("GROQ_API_KEY", "GROK_API_KEY", "XAI_API_KEY", "OPENAI_API_KEY")):
        print("Error: Set an API key in .env first.")
        sys.exit(1)

    jd_path = Path(args.jd)
    if not jd_path.is_file():
        print(f"Error: Job description file not found: {jd_path}")
        sys.exit(1)

    resume_paths = []
    for pattern in args.resumes:
        p = Path(pattern)
        if p.is_file():
            resume_paths.append(p)
        elif p.is_dir():
            resume_paths.extend(p.glob("*.pdf"))
            resume_paths.extend(p.glob("*.docx"))

    if not resume_paths:
        print("Error: No PDF or DOCX resumes found.")
        sys.exit(1)

    job_description = jd_path.read_text(encoding="utf-8")
    weights = {"semantic": 35, "skills": 35, "ai": 30}

    from agents.ranking_agent import rank_candidates
    from resume_core.pipeline import run_screening_from_paths
    from resume_core.scoring import get_embedding_model

    print(f"Screening {len(resume_paths)} resume(s)...")
    get_embedding_model()
    results = run_screening_from_paths(resume_paths, job_description, weights)
    ranked = rank_candidates(results)

    out = Path(args.output)
    ranked.drop(columns=["Analysis"], errors="ignore").to_csv(out, index=False)
    print(f"Done. Results saved to {out}")
    print(ranked[["Rank", "Candidate", "Composite Score", "Verdict"]].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="AI Resume Screening Agent")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Start Streamlit UI (default)")
    sub.add_parser("check", help="Verify Python dependencies and API key")

    screen_p = sub.add_parser("screen", help="Screen resumes from CLI")
    screen_p.add_argument("--jd", required=True, help="Job description .txt file")
    screen_p.add_argument("--resumes", nargs="+", required=True, help="Resume files or folders")
    screen_p.add_argument("--output", default="screening_results.csv", help="Output CSV path")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check()
    elif args.command == "screen":
        cmd_screen(args)
    else:
        cmd_serve()


if __name__ == "__main__":
    main()
