CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding-top: 1.5rem;
    max-width: 1200px;
}

.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 40px rgba(79, 70, 229, 0.25);
}

.hero h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 0.4rem 0;
    color: white !important;
}

.hero p {
    margin: 0;
    opacity: 0.92;
    font-size: 1.05rem;
    color: rgba(255,255,255,0.95) !important;
}

.pill {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 1rem;
}

.pill-ok { background: rgba(16, 185, 129, 0.25); color: #d1fae5; border: 1px solid rgba(16,185,129,0.5); }
.pill-warn { background: rgba(251, 191, 36, 0.25); color: #fef3c7; border: 1px solid rgba(251,191,36,0.5); }

.step-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.25rem;
    height: 100%;
}

.step-num {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
}

.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
}

.metric-card .label { color: #64748b; font-size: 0.85rem; font-weight: 500; margin: 0; }
.metric-card .value { color: #0f172a; font-size: 1.75rem; font-weight: 700; margin: 0.25rem 0 0 0; }

.badge-hire { background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 0.8rem; }
.badge-maybe { background: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 0.8rem; }
.badge-reject { background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 0.8rem; }

.top-candidate {
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
    border: 2px solid #86efac;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.sidebar-brand {
    font-size: 1.1rem;
    font-weight: 700;
    color: #4f46e5;
    margin-bottom: 0.25rem;
}

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fafafa 0%, #f1f5f9 100%);
}
</style>
"""


def inject_theme():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def hero(title, subtitle, status_ok, provider=None):
    import streamlit as st
    pill = (
        f'<span class="pill pill-ok">● Connected — {provider.upper()}</span>'
        if status_ok and provider
        else '<span class="pill pill-warn">● API key required</span>'
    )
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p>{pill}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value):
    return f"""
    <div class="metric-card">
        <p class="label">{label}</p>
        <p class="value">{value}</p>
    </div>
    """


def verdict_badge(verdict):
    css = {"Hire": "badge-hire", "Maybe": "badge-maybe", "Reject": "badge-reject"}
    cls = css.get(verdict, "badge-maybe")
    return f'<span class="{cls}">{verdict}</span>'
