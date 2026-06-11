import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for mod in list(sys.modules):
    if mod == "utils" or mod.startswith("utils."):
        del sys.modules[mod]
for folder in ROOT.rglob("__pycache__"):
    shutil.rmtree(folder, ignore_errors=True)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def has_llm_api_key():
    return bool(
        os.getenv("GROQ_API_KEY")
        or os.getenv("GROK_API_KEY")
        or os.getenv("XAI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )


def get_active_provider():
    forced = os.getenv("LLM_PROVIDER", "").lower().strip()
    if forced:
        return forced if has_llm_api_key() else None
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"):
        return "grok"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return None


import pandas as pd
import streamlit as st

from agents.ranking_agent import rank_candidates
from resume_core.pipeline import run_screening
from resume_core.scoring import get_embedding_model
from ui.theme import hero, inject_theme, metric_card, verdict_badge

st.set_page_config(
    page_title="ResumeAI — Smart Screening",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

if "results" not in st.session_state:
    st.session_state.results = None

provider = get_active_provider()
hero(
    "ResumeAI",
    "Upload resumes, match against your job description, and get ranked candidates with AI insights.",
    has_llm_api_key(),
    provider,
)

if not has_llm_api_key():
    st.error("Add `GROQ_API_KEY` to `.env` and restart with `python main.py`")

with st.sidebar:
    st.markdown('<p class="sidebar-brand">✦ ResumeAI</p>', unsafe_allow_html=True)
    st.caption("Intelligent hiring assistant")

    with st.expander("⚙️ Scoring weights", expanded=False):
        st.caption("Defaults work great — tweak only if needed.")
        weights = {
            "semantic": st.slider("Semantic match", 0, 100, 35),
            "skills": st.slider("Skills overlap", 0, 100, 35),
            "ai": st.slider("AI fit score", 0, 100, 30),
        }

    st.divider()
    st.markdown("**Pipeline**")
    st.markdown(
        """
        1. Parse PDF / DOCX resumes  
        2. Embed & score with FAISS  
        3. Extract skill gaps  
        4. Groq AI analysis  
        5. Rank & export
        """
    )
    if provider:
        st.success(f"Model provider: **{provider.upper()}**")

tab_screen, tab_results, tab_export = st.tabs(["Upload & Screen", "Analytics", "Export"])

with tab_screen:
    st.markdown("### Get started in 3 steps")

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            '<div class="step-card"><div class="step-num">1</div><strong>Upload</strong><br><span style="color:#64748b">PDF or DOCX resumes</span></div>',
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            '<div class="step-card"><div class="step-num">2</div><strong>Describe role</strong><br><span style="color:#64748b">Paste job description</span></div>',
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            '<div class="step-card"><div class="step-num">3</div><strong>Screen</strong><br><span style="color:#64748b">AI ranks candidates</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    col_upload, col_jd = st.columns([1, 1], gap="large")

    with col_upload:
        with st.container(border=True):
            st.markdown("#### 📄 Resumes")
            uploaded_files = st.file_uploader(
                "Drop files here",
                type=["pdf", "docx"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            if uploaded_files:
                for f in uploaded_files:
                    st.markdown(f"✓ `{f.name}`")

    with col_jd:
        with st.container(border=True):
            st.markdown("#### 📋 Job description")
            job_description = st.text_area(
                "Job description",
                height=200,
                placeholder="e.g. We need a Python developer with SQL, AWS, and 3+ years experience...",
                label_visibility="collapsed",
            )

    st.markdown("")
    screen = st.button(
        "Run AI Screening →",
        type="primary",
        disabled=not has_llm_api_key(),
        use_container_width=True,
    )

    if screen:
        if not uploaded_files or not job_description.strip():
            st.warning("Please upload at least one resume and paste a job description.")
        else:
            progress = st.progress(0, text="Starting...")
            status = st.empty()
            live = st.container()

            def on_progress(done, total, name, stage):
                progress.progress(done / total if total else 0, text=f"{stage} — {name}")
                status.markdown(f"⏳ **{name}** · {stage}")

            with st.spinner("Loading AI models (first run may take a minute)..."):
                get_embedding_model()

            results = run_screening(uploaded_files, job_description, weights, on_progress)

            if not results:
                st.error("Could not extract text from the uploaded files.")
            else:
                st.session_state.results = rank_candidates(results)
                progress.progress(1.0, text="Complete!")
                status.success(f"Done — {len(results)} candidate(s) ranked. Open **Analytics** tab →")

                top = st.session_state.results.iloc[0]
                with live:
                    st.markdown(
                        f"""<div class="top-candidate">
                        <strong>🏆 Top match:</strong> {top['Candidate']}
                        &nbsp;·&nbsp; <strong>{top['Composite Score']}%</strong>
                        &nbsp;·&nbsp; {verdict_badge(top['Verdict'])}
                        </div>""",
                        unsafe_allow_html=True,
                    )

with tab_results:
    if st.session_state.results is None:
        st.info("👆 Upload resumes and run screening to see analytics here.")
    else:
        df = st.session_state.results

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(metric_card("Candidates", len(df)), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card("Top match", f"{df['Composite Score'].max()}%"), unsafe_allow_html=True)
        with m3:
            st.markdown(metric_card("Average score", f"{round(df['Composite Score'].mean(), 1)}%"), unsafe_allow_html=True)
        with m4:
            st.markdown(metric_card("Hire verdicts", int((df["Verdict"] == "Hire").sum())), unsafe_allow_html=True)

        st.markdown("---")

        left, right = st.columns([1.2, 1])
        with left:
            st.markdown("#### Score leaderboard")
            chart = df.set_index("Candidate")[["Composite Score"]].sort_values("Composite Score")
            st.bar_chart(chart, height=340, color="#4f46e5")

        with right:
            st.markdown("#### Score breakdown")
            for _, row in df.head(5).iterrows():
                st.markdown(f"**#{row['Rank']} {row['Candidate']}** — {row['Composite Score']}%")
                st.progress(min(row["Composite Score"] / 100, 1.0))

        st.markdown("#### Full rankings")
        show = df[
            ["Rank", "Candidate", "Composite Score", "Tier", "Verdict",
             "Semantic Score", "Skills Score", "AI Fit Score"]
        ].copy()
        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Composite Score": st.column_config.ProgressColumn(
                    "Match %", format="%d%%", min_value=0, max_value=100
                ),
                "Semantic Score": st.column_config.NumberColumn(format="%d%%"),
                "Skills Score": st.column_config.NumberColumn(format="%d%%"),
                "AI Fit Score": st.column_config.NumberColumn(format="%d%%"),
                "Verdict": st.column_config.TextColumn("Verdict"),
            },
        )

        st.markdown("#### Candidate profiles")
        for _, row in df.iterrows():
            with st.container(border=True):
                head_l, head_r = st.columns([4, 1])
                with head_l:
                    st.markdown(f"### #{row['Rank']} · {row['Candidate']}")
                    st.caption(row["Tier"])
                with head_r:
                    st.markdown(verdict_badge(row["Verdict"]), unsafe_allow_html=True)
                    st.markdown(f"**{row['Composite Score']}%** match")

                st.markdown(row["Summary"])
                st.info(row["Recommendation"])

                a, b, c = st.columns(3)
                a.metric("Semantic", f"{row['Semantic Score']}%")
                b.metric("Skills", f"{row['Skills Score']}%")
                c.metric("AI fit", f"{row['AI Fit Score']}%")

                sk1, sk2 = st.columns(2)
                with sk1:
                    st.markdown(f"✅ **Matched:** {row['Matched Skills']}")
                with sk2:
                    st.markdown(f"⚠️ **Missing:** {row['Missing Skills']}")

                questions = row.get("Interview Questions") or []
                if questions:
                    st.markdown("**Interview questions**")
                    for i, q in enumerate(questions, 1):
                        st.markdown(f"{i}. {q}")

with tab_export:
    if st.session_state.results is None:
        st.info("Run a screening session first to export results.")
    else:
        df = st.session_state.results.drop(columns=["Analysis"], errors="ignore")
        st.markdown("#### Download reports")

        e1, e2 = st.columns(2)
        with e1:
            st.download_button(
                "📥 Download CSV",
                df.to_csv(index=False),
                "screening_results.csv",
                "text/csv",
                use_container_width=True,
                type="primary",
            )
        with e2:
            records = df.to_dict("records")
            st.download_button(
                "📥 Download JSON",
                json.dumps(records, indent=2, default=str),
                "screening_results.json",
                "application/json",
                use_container_width=True,
            )
        st.markdown("#### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
