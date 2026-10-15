"""Dark theme CSS for the Streamlit UI."""

DARK_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #070a12;
  --panel: rgba(15, 23, 42, 0.74);
  --panel-strong: rgba(17, 24, 39, 0.94);
  --border: rgba(148, 163, 184, 0.22);
  --text: #e5e7eb;
  --muted: #94a3b8;
  --cyan: #22d3ee;
  --violet: #8b5cf6;
  --pink: #ec4899;
  --green: #34d399;
}

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
  color: var(--text);
  background:
    radial-gradient(circle at 18% 8%, rgba(124, 58, 237, 0.34), transparent 34%),
    radial-gradient(circle at 82% 18%, rgba(34, 211, 238, 0.24), transparent 30%),
    radial-gradient(circle at 45% 88%, rgba(236, 72, 153, 0.14), transparent 36%),
    linear-gradient(135deg, #050711 0%, #090d19 48%, #030712 100%);
}

.block-container {
  max-width: 1320px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.94));
  border-right: 1px solid rgba(34, 211, 238, 0.16);
}

[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: #f8fafc;
}

.side-logo {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  margin: 0.35rem 0 1.2rem;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--cyan), var(--violet) 52%, var(--pink));
  color: #020617;
  font-weight: 900;
  letter-spacing: -0.08em;
  box-shadow: 0 0 34px rgba(34, 211, 238, 0.28);
}

.top-title {
  position: fixed;
  top: 0.72rem;
  right: 1.1rem;
  z-index: 999;
  padding: 0.42rem 0.7rem;
  border: 1px solid rgba(34, 211, 238, 0.26);
  border-radius: 999px;
  background: rgba(2, 6, 23, 0.72);
  color: #cbd5e1;
  font-size: 0.82rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  backdrop-filter: blur(12px);
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0 0.8rem;
}

.section-index {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  color: #020617;
  background: linear-gradient(135deg, var(--cyan), var(--green));
  font-weight: 900;
  box-shadow: 0 0 28px rgba(34, 211, 238, 0.22);
}

.section-heading h2 {
  margin: 0;
  color: #f8fafc;
  font-size: 1.55rem;
  letter-spacing: -0.04em;
}

.section-heading p {
  margin: 0.15rem 0 0;
  color: var(--muted);
}

.signal-card {
  min-height: 132px;
  padding: 1.2rem;
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.4), rgba(15, 23, 42, 0.8));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
}

.signal-card strong {
  color: #f8fafc;
  font-size: 1.02rem;
}

.signal-card p {
  margin: 0.55rem 0 0;
  color: #a7b4c8;
  line-height: 1.55;
}

.signal-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 0.55rem;
  border-radius: 999px;
  background: var(--green);
  box-shadow: 0 0 18px var(--green);
}

.progress-panel {
  margin: 1rem 0;
  padding: 0.9rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.62);
}

.task-card {
  margin: 0.5rem 0 1rem;
  padding: 1rem;
  border: 1px solid rgba(34, 211, 238, 0.24);
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(8, 47, 73, 0.55), rgba(30, 41, 59, 0.68)),
    radial-gradient(circle at 100% 0%, rgba(52, 211, 153, 0.18), transparent 42%);
}

.task-label {
  color: #67e8f9;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.task-title {
  margin-top: 0.25rem;
  color: #f8fafc;
  font-size: 1.15rem;
  font-weight: 850;
  letter-spacing: -0.04em;
}

.task-note {
  margin-top: 0.35rem;
  color: #a7b4c8;
  font-size: 0.84rem;
  line-height: 1.45;
}

.progress-panel h3 {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
}

.progress-row {
  margin: 0.55rem 0;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.22rem;
  color: #cbd5e1;
  font-size: 0.82rem;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(51, 65, 85, 0.9);
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--cyan), var(--green));
}

[data-testid="stFileUploader"],
[data-testid="stDataFrameResizable"],
[data-testid="stMetric"],
[data-testid="stTabs"] {
  border-radius: 24px;
}

[data-testid="stFileUploader"] section {
  border: 1px dashed rgba(34, 211, 238, 0.38);
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.72);
}

[data-testid="stMetric"] {
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.78), rgba(30, 41, 59, 0.54));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.stButton > button, .stDownloadButton > button {
  width: 100%;
  border: 1px solid rgba(34, 211, 238, 0.28);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.95), rgba(124, 58, 237, 0.94));
  color: white;
  font-weight: 800;
  letter-spacing: -0.01em;
  box-shadow: 0 14px 32px rgba(37, 99, 235, 0.22);
  transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-1px);
  filter: brightness(1.08);
  box-shadow: 0 18px 44px rgba(34, 211, 238, 0.28);
}

[data-testid="stAlert"] {
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(15, 23, 42, 0.7);
}

.stCodeBlock pre {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  background: rgba(2, 6, 23, 0.82) !important;
}

input, textarea {
  border-radius: 14px !important;
}

hr {
  border-color: rgba(148, 163, 184, 0.16);
}
</style>
"""


def inject_dark_style(st: object) -> None:
    """Add the dark theme CSS to the Streamlit page."""
    st.markdown(DARK_STYLE, unsafe_allow_html=True)
