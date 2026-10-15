"""Neutral workspace theme for the Streamlit UI: light gray canvas, flat panels, one blue accent."""

APP_STYLE = """
<style>
:root {
  --bg: #f6f7f9;
  --panel: #ffffff;
  --ink: #1f2937;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #2563eb;
  --accent-soft: #eff6ff;
}

html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}

.stApp {
  background: var(--bg);
  color: var(--ink);
}

.block-container {
  max-width: 1200px;
  padding-top: 2rem;
  padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
  background: var(--panel);
  border-right: 1px solid var(--line);
}

.side-logo {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  margin: 0.25rem 0 1rem;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 700;
  font-size: 0.8rem;
}

.top-title {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.5rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--line);
}

.section-index {
  display: grid;
  place-items: center;
  min-width: 26px;
  height: 26px;
  padding: 0 0.4rem;
  border-radius: 6px;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.section-heading h2 {
  margin: 0;
  color: var(--ink);
  font-size: 1.1rem;
  font-weight: 600;
}

[data-testid="stFileUploader"] section {
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: var(--panel);
}

[data-testid="stMetric"] {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: var(--panel);
  border: 1px solid var(--line);
}

[data-testid="stAlert"] {
  border-radius: 8px;
}

.stButton > button, .stDownloadButton > button {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  color: var(--ink);
  font-weight: 600;
  padding: 0.5rem 0.9rem;
}

.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
}

.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
  color: #ffffff;
}

.stButton > button:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  border-color: var(--line);
}

[data-testid="stExpander"] {
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--panel);
}

.stCodeBlock pre {
  border-radius: 6px;
  border: 1px solid var(--line);
}

input, textarea, [data-baseweb="select"] > div {
  border-radius: 6px !important;
}
</style>
"""


def inject_app_style(st: object) -> None:
    """Add the workspace theme CSS to the Streamlit page.

    Args:
        st: The imported ``streamlit`` module, passed in so this file stays free of Streamlit imports.
    """
    st.markdown(APP_STYLE, unsafe_allow_html=True)
