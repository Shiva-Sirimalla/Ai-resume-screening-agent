#!/usr/bin/env python3
"""Install dependencies and create .env — run: python setup_env.py"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def install_requirements():
    req = ROOT / "requirements.txt"
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])


def create_env_file():
    env = ROOT / ".env"
    example = ROOT / ".env.example"
    if env.exists():
        print(".env already exists — skipping")
        return
    if example.exists():
        shutil.copy(example, env)
        print("Created .env from .env.example — add your GROQ_API_KEY")
    else:
        env.write_text("GROQ_API_KEY=\nLLM_PROVIDER=groq\n", encoding="utf-8")
        print("Created .env — add your GROQ_API_KEY")


def main():
    install_requirements()
    create_env_file()
    print("\nSetup complete. Next steps:")
    print("  1. Edit .env and set GROQ_API_KEY")
    print("  2. python main.py check")
    print("  3. python main.py")


if __name__ == "__main__":
    main()
