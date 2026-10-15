"""Soft pastel theme for the Streamlit UI: light background, rounded corners, friendly type."""

APP_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

:root {
  --bg: #fff8fb;
  --card: #ffffff;
  --ink: #4b4358;
  --muted: #8f84a0;
  --pink: #f9a8d4;
  --pink-soft: #fce7f3;
  --lilac: #ddd6fe;
  --mint: #bbf7d0;
  --border: #f3e8f0;
}

html, body, [class*="css"] {
  font-family: 'Nunito', system-ui, -apple-system, sans-serif;
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
  background: #fdf4f9;
  border-right: 1px solid var(--border);
}

.side-logo {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  margin: 0.25rem 0 1rem;
  border-radius: 18px;
  background: var(--pink);
  color: #ffffff;
  font-weight: 800;
  font-size: 1.05rem;
}

.top-title {
  display: inline-block;
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  background: var(--pink-soft);
  color: #be185d;
  font-size: 0.9rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  margin: 1.6rem 0 0.8rem;
}

.section-index {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--lilac);
  color: #5b21b6;
  font-weight: 800;
  font-size: 0.95rem;
}

.section-heading h2 {
  margin: 0;
  color: var(--ink);
  font-size: 1.4rem;
  font-weight: 800;
}

.editor-heading .section-index { background: var(--mint); color: #166534; }
.export-heading .section-index { background: var(--pink-soft); color: #be185d; }

[data-testid="stFileUploader"] section {
  border: 2px dashed var(--pink);
  border-radius: 20px;
  background: var(--card);
}

[data-testid="stMetric"] {
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: var(--card);
  border: 1px solid var(--border);
}

[data-testid="stAlert"] {
  border-radius: 16px;
}

.stButton > button, .stDownloadButton > button {
  width: 100%;
  border: none;
  border-radius: 999px;
  background: var(--pink);
  color: #4a044e;
  font-weight: 800;
  padding: 0.55rem 1rem;
  transition: background 150ms ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
  background: #f472b6;
  color: #ffffff;
}

.stButton > button:disabled {
  background: #f3f0f5;
  color: #b8afc2;
}

[data-testid="stExpander"] {
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--card);
}

.stCodeBlock pre {
  border-radius: 16px;
  border: 1px solid var(--border);
}

input, textarea, [data-baseweb="select"] > div {
  border-radius: 12px !important;
}

hr {
  border-color: var(--border);
}
</style>
"""


def inject_app_style(st: object) -> None:
    """Add the pastel theme CSS to the Streamlit page.

    Args:
        st: The imported ``streamlit`` module, passed in so this file stays free of Streamlit imports.
    """
    st.markdown(APP_STYLE, unsafe_allow_html=True)
