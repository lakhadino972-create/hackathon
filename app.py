"""
app.py
------
AI Smart Civic Services - modern Streamlit frontend.

Backend (unchanged):
  - database.py    -> SQLite storage, filters and statistics queries
  - classifier.py  -> trained scikit-learn model that predicts the category

This file only changes how the app LOOKS and how results are presented.
Run locally with:   python -m streamlit run app.py
"""

import html
import os
import re
import sqlite3
import statistics
from collections import Counter
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from database import (
    init_db, add_complaint, get_all_complaints, get_complaint_by_id,
    update_status, filter_complaints, get_category_counts,
    get_status_counts, get_resolution_times,
)

# The AI model is loaded when classifier.py is imported. If that fails
# (missing .pkl, version mismatch...) the rest of the app still works.
try:
    from classifier import classify_complaint
    CLASSIFIER_ERROR = None
except Exception as error:
    classify_complaint = None
    CLASSIFIER_ERROR = str(error)

# ---------------------------------------------------------------------------
# Page setup and constants
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Smart Civic Services", page_icon="🏙️", layout="wide")

UPLOAD_DIR = "uploads"
VALID_STATUSES = ["Open", "Assigned", "In Progress", "Resolved"]
VALID_CATEGORIES = ["Road", "Water", "Drainage", "Waste", "Electricity", "Safety"]

# One consistent dark colour system used by cards, badges and charts
CARD_BG = "#1E293B"
ACCENT = "#38BDF8"
TEXT = "#F8FAFC"
TEXT_SECONDARY = "#CBD5E1"
GRID = "#334155"
STATUS_COLORS = {
    "Open": "#EF4444",
    "Assigned": "#F59E0B",
    "In Progress": "#3B82F6",
    "Resolved": "#22C55E",
}
MAX_CARDS = 60  # keeps the page fast when there are many complaints

# ---------------------------------------------------------------------------
# Custom CSS (all styling and animation lives here)
# ---------------------------------------------------------------------------
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg:#0F172A; --card:#1E293B; --card-2:#273449; --border:#334155; --border-strong:#64748B;
  --accent:#38BDF8; --accent-2:#06B6D4; --text:#F8FAFC; --text-2:#CBD5E1; --muted:#94A3B8;
  --green:#22C55E; --amber:#F59E0B; --blue:#3B82F6; --red:#EF4444;
  --shadow:0 1px 2px rgba(0,0,0,.30), 0 10px 28px rgba(0,0,0,.35);
  --shadow-hover:0 2px 4px rgba(0,0,0,.35), 0 18px 36px rgba(0,0,0,.50);
  color-scheme: dark;
}

/* ---------- Base (dark page, readable text) ---------- */
.stApp {
  background: radial-gradient(900px 420px at 88% -8%, rgba(56,189,248,.14), transparent 60%),
              radial-gradient(700px 380px at -5% 30%, rgba(6,182,212,.08), transparent 60%), #0F172A;
  color: var(--text);
  font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
}
.stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color: var(--text); }
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
[data-testid="stAppDeployButton"], .stDeployButton { display: none; }
.block-container { max-width: 1180px; padding-top: 1.2rem; padding-bottom: 3rem; }
div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] p { color: var(--muted) !important; }

/* ---------- Animations (subtle, disabled for reduced-motion users) ---------- */
@keyframes fadeUp { from {opacity:0; transform:translateY(14px);} to {opacity:1; transform:none;} }
@keyframes floaty { 0%,100% {transform:translateY(0);} 50% {transform:translateY(-14px);} }
.fade-in { animation: fadeUp .55s ease both; }
@media (prefers-reduced-motion: reduce) {
  .fade-in, .hero::before, .hero::after { animation: none !important; }
  * { transition: none !important; }
}

/* ---------- Hero ---------- */
.hero { position:relative; overflow:hidden; border-radius:22px; padding:2.4rem 2.2rem 2rem; margin-bottom:1.4rem;
  background:linear-gradient(135deg,#1E293B 0%,#12304F 55%,#0B4A63 100%); border:1px solid rgba(56,189,248,.28); box-shadow:0 18px 44px rgba(0,0,0,.45); }
.hero::before, .hero::after { content:""; position:absolute; border-radius:50%; animation:floaty 9s ease-in-out infinite; }
.hero::before { width:280px; height:280px; background:var(--accent); opacity:.16; top:-90px; right:-60px; }
.hero::after { width:200px; height:200px; background:var(--accent-2); opacity:.12; bottom:-100px; left:38%; animation-delay:-4s; }
.hero > * { position:relative; z-index:1; }
.hero-pill { display:inline-block; padding:.28rem .85rem; border-radius:999px; margin-bottom:.9rem; font-size:.74rem; font-weight:600;
  letter-spacing:.06em; text-transform:uppercase; color:#7DD3FC !important; background:rgba(56,189,248,.12); border:1px solid rgba(56,189,248,.35); }
.stMarkdown .hero h1 { color:#F8FAFC !important; font-size:2.6rem; line-height:1.1; font-weight:800; letter-spacing:-.02em; margin:0 0 .5rem; padding:0; }
.stMarkdown .hero .hero-tagline { color:#7DD3FC !important; font-size:1.15rem; font-weight:500; margin:0 0 .6rem; }
.stMarkdown .hero .hero-desc { color:#CBD5E1 !important; max-width:660px; font-size:.97rem; line-height:1.6; margin:0 0 1.4rem; }
.hero-stats { display:flex; flex-wrap:wrap; gap:.8rem; }
.hero-stat { min-width:130px; padding:.7rem 1rem; border-radius:14px; font-size:.8rem; color:#CBD5E1; background:rgba(15,23,42,.45); border:1px solid rgba(148,163,184,.25); }
.hero-stat span { display:block; font-size:1.65rem; font-weight:800; color:#F8FAFC; line-height:1.15; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap:6px; padding:6px; background:var(--card); border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); overflow-x:auto; }
.stTabs [data-baseweb="tab"] { height:44px; padding:0 20px; border-radius:11px; background:transparent; transition:background .2s ease; }
.stTabs [data-baseweb="tab"] p { font-weight:600; color:var(--text-2); font-size:.95rem; }
.stTabs [data-baseweb="tab"]:hover { background:var(--card-2); }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,var(--accent),var(--accent-2)) !important; }
.stTabs [aria-selected="true"] p { color:#0F172A !important; font-weight:700; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }

/* ---------- Buttons (dark text on bright cyan = high contrast) ---------- */
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
  width:100%; border:none; border-radius:12px; padding:.62rem 1.2rem; color:#0F172A; font-weight:700;
  background:linear-gradient(135deg,var(--accent),var(--accent-2)); box-shadow:0 6px 18px rgba(56,189,248,.25);
  transition:transform .18s ease, box-shadow .18s ease, filter .18s ease; }
.stButton > button p, div[data-testid="stFormSubmitButton"] > button p { color:#0F172A !important; font-weight:700; }
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { transform:translateY(-2px); filter:brightness(1.08); box-shadow:0 10px 24px rgba(56,189,248,.38); color:#0F172A; border:none; }
.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active { transform:translateY(0); }
.stButton > button:focus-visible, div[data-testid="stFormSubmitButton"] > button:focus-visible { outline:3px solid #F8FAFC; outline-offset:2px; }

/* ---------- Forms and inputs (visible labels, text, placeholders, borders, focus) ---------- */
div[data-testid="stForm"] { background:var(--card); border:1px solid var(--border); border-radius:18px; padding:1.3rem 1.4rem .8rem; box-shadow:var(--shadow); }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color:var(--text-2) !important; font-weight:600; }
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
  background:#0F172A !important; border:1px solid var(--border-strong) !important; border-radius:10px !important; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within, div[data-baseweb="select"] > div:focus-within {
  border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(56,189,248,.28) !important; }
.stApp input, .stApp textarea { color:var(--text) !important; -webkit-text-fill-color:var(--text); caret-color:var(--accent); }
.stApp input::placeholder, .stApp textarea::placeholder { color:var(--muted) !important; -webkit-text-fill-color:var(--muted); opacity:1 !important; }
[data-testid="stFileUploaderDropzone"] { background:#0F172A; border:1.5px dashed var(--border-strong); border-radius:12px; }

/* ---------- Expanders, tables, charts, messages ---------- */
div[data-testid="stExpander"] { background:var(--card); border:1px solid var(--border); border-radius:14px; }
div[data-testid="stExpander"] summary p { color:var(--text); font-weight:600; }
div[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; overflow:hidden; }
div[data-testid="stVegaLiteChart"] { background:var(--card); border:1px solid var(--border); border-radius:16px; padding:.8rem; box-shadow:var(--shadow); }
div[data-testid="stAlert"] { border-radius:12px; border:1px solid var(--border); }
div[data-testid="stAlert"] p { color:var(--text) !important; }

/* ---------- Generic cards and text ---------- */
.section-title { font-size:1.15rem; font-weight:700; color:var(--text); margin:1.1rem 0 .15rem; }
.section-sub { color:var(--muted); font-size:.88rem; margin-bottom:.7rem; }
.panel { background:var(--card); border:1px solid var(--border); border-radius:18px; padding:1.2rem 1.3rem; box-shadow:var(--shadow); margin-bottom:1rem; }
.panel h4 { margin:0 0 .6rem; color:var(--text); font-size:1rem; font-weight:700; }
.panel ul { margin:0; padding-left:1.1rem; color:var(--text-2); font-size:.9rem; line-height:1.7; }
.panel-text { color:var(--text-2); font-size:.92rem; line-height:1.6; margin:.7rem 0 .3rem; }
.panel-text b { color:var(--text); }
.empty { text-align:center; padding:2.2rem 1rem; border:1.5px dashed var(--border-strong); border-radius:16px; background:var(--card); color:var(--text-2); }
.empty b { display:block; color:var(--text); font-size:1.05rem; margin-bottom:.3rem; }
.notice { margin-top:.8rem; padding:.6rem .8rem; border-radius:10px; background:rgba(245,158,11,.16); border:1px solid rgba(245,158,11,.4); color:#FCD34D; font-size:.85rem; }
.count-pill { display:inline-block; padding:.25rem .8rem; border-radius:999px; background:rgba(56,189,248,.14); border:1px solid rgba(56,189,248,.35); color:#7DD3FC; font-weight:600; font-size:.82rem; margin:.3rem 0 .8rem; }

/* ---------- Steps ---------- */
.steps { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:.7rem; }
.step { padding:.8rem; border-radius:14px; background:var(--bg); border:1px solid var(--border); transition:transform .2s ease, border-color .2s ease; }
.step:hover { transform:translateY(-3px); border-color:var(--accent); }
.step-num { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#0F172A; font-weight:800; font-size:.85rem; background:linear-gradient(135deg,var(--accent),var(--accent-2)); margin-bottom:.45rem; }
.step b { display:block; color:var(--text); font-size:.9rem; }
.step span { color:var(--text-2); font-size:.8rem; line-height:1.4; }

/* ---------- Chips and badges ---------- */
.chip { display:inline-block; padding:.2rem .65rem; margin:.15rem .2rem .15rem 0; border-radius:999px; font-size:.78rem; font-weight:600; color:#7DD3FC; background:rgba(56,189,248,.14); border:1px solid rgba(56,189,248,.3); }
.chip-ai { color:#0F172A; font-weight:700; background:linear-gradient(135deg,var(--accent),var(--accent-2)); border:none; font-size:.9rem; padding:.3rem .9rem; }
.chip-muted { color:var(--text-2); background:var(--card-2); border:1px solid var(--border-strong); }
.badge { display:inline-block; padding:.22rem .7rem; border-radius:999px; font-size:.75rem; font-weight:700; border:1px solid transparent; }
.badge-open { background:rgba(239,68,68,.18); color:#FCA5A5; border-color:rgba(239,68,68,.45); }
.badge-assigned { background:rgba(245,158,11,.18); color:#FCD34D; border-color:rgba(245,158,11,.45); }
.badge-in-progress { background:rgba(59,130,246,.22); color:#93C5FD; border-color:rgba(59,130,246,.5); }
.badge-resolved { background:rgba(34,197,94,.18); color:#86EFAC; border-color:rgba(34,197,94,.45); }

/* ---------- KPI cards ---------- */
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:.9rem; margin:.4rem 0 1.2rem; }
.kpi { background:var(--card); border:1px solid var(--border); border-top:4px solid var(--accent); border-radius:16px; padding:1rem 1.1rem; box-shadow:var(--shadow); transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
.kpi:hover { transform:translateY(-3px); box-shadow:var(--shadow-hover); border-color:var(--border-strong); }
.kpi-label { font-size:.74rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
.kpi-value { font-size:1.8rem; font-weight:800; color:var(--text); line-height:1.25; margin-top:.2rem; }
.kpi-sub { font-size:.78rem; color:var(--muted); min-height:1em; }
.kpi.open { border-top-color:var(--red); } .kpi.assigned { border-top-color:var(--amber); }
.kpi.progress { border-top-color:var(--blue); } .kpi.resolved { border-top-color:var(--green); }

/* ---------- Complaint cards ---------- */
.card-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:.9rem; }
.complaint-card { background:var(--card); border:1px solid var(--border); border-radius:16px; padding:1rem 1.1rem; box-shadow:var(--shadow); transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease; }
.complaint-card:hover { transform:translateY(-3px); box-shadow:var(--shadow-hover); border-color:var(--accent); }
.cc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem; }
.cc-id { font-weight:800; color:var(--text); }
.cc-desc { color:var(--text-2); font-size:.9rem; line-height:1.5; margin:0 0 .6rem; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.cc-loc { color:var(--muted); font-size:.8rem; }
.cc-date { color:var(--muted); font-size:.75rem; margin-top:.4rem; }

/* ---------- Submission result card ---------- */
.result-card { background:var(--card); border:1px solid rgba(34,197,94,.4); border-left:6px solid var(--green); border-radius:18px; padding:1.2rem 1.4rem; box-shadow:var(--shadow); margin-bottom:1rem; }
.result-head { display:flex; gap:.8rem; align-items:center; margin-bottom:1rem; }
.result-check { width:38px; height:38px; border-radius:50%; background:rgba(34,197,94,.18); color:#86EFAC; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.1rem; }
.result-title { font-weight:700; color:var(--text); font-size:1.1rem; }
.result-sub { color:var(--text-2); font-size:.85rem; }
.result-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.8rem; }
.result-label { font-size:.72rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; margin-bottom:.2rem; }
.result-value { color:var(--text); font-weight:600; font-size:.95rem; }
</style>
"""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def render(markup):
    """Show an HTML block. Indentation and blank lines are removed first,
    because Markdown would otherwise treat indented HTML as code."""
    cleaned = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def esc(value):
    """Escape user text before placing it inside HTML (prevents HTML injection)."""
    return html.escape(str(value)) if value is not None else ""


def status_slug(status):
    return re.sub(r"[^a-z]+", "-", str(status).lower()).strip("-")


def friendly_time(hours):
    """Turn hours into minutes / hours / days, whichever reads best."""
    minutes = hours * 60
    if minutes < 1:
        return "under 1 min"
    if hours < 1:
        return f"{minutes:.0f} min"
    if hours < 24:
        return f"{hours:.1f} hours"
    return f"{hours / 24:.1f} days"


def show_chart(chart):
    """Draw an Altair chart full-width with dark-theme colours
    (works on old and new Streamlit versions)."""
    chart = (
        chart.configure(background=CARD_BG)
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY, gridColor=GRID,
                        domainColor="#475569", tickColor="#475569", labelFontSize=12, titleFontSize=12)
        .configure_legend(labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY, labelFontSize=12)
    )
    try:
        st.altair_chart(chart, theme=None, width="stretch")
    except TypeError:
        st.altair_chart(chart, theme=None, use_container_width=True)


def empty_state(title, message):
    render(f'<div class="empty fade-in"><b>{esc(title)}</b>{esc(message)}</div>')


def kpi_grid(cards):
    """cards = list of (label, value, sub_text, tone). Tone is a CSS class or ''."""
    parts = []
    for index, (label, value, sub, tone) in enumerate(cards):
        parts.append(
            f'<div class="kpi {tone} fade-in" style="animation-delay:{index * 0.06:.2f}s">'
            f'<div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value">{esc(value)}</div>'
            f'<div class="kpi-sub">{esc(sub)}</div></div>'
        )
    render('<div class="kpi-grid">' + "".join(parts) + "</div>")


def complaint_cards(records):
    """Show complaints as a responsive grid of cards."""
    shown = records[:MAX_CARDS]
    parts = []
    for index, c in enumerate(shown):
        status = c.get("status") or "Open"
        category = c.get("category") or "Unclassified"
        resolved = f" &middot; Resolved {esc(c['resolved_date'])}" if c.get("resolved_date") else ""
        parts.append(
            f'<div class="complaint-card fade-in" style="animation-delay:{min(index * 0.04, 0.4):.2f}s">'
            f'<div class="cc-top"><span class="cc-id">#{c["complaint_id"]}</span>'
            f'<span class="badge badge-{status_slug(status)}">{esc(status)}</span></div>'
            f'<p class="cc-desc">{esc(c.get("description"))}</p>'
            f'<span class="chip">{esc(category)}</span> <span class="cc-loc">{esc(c.get("location"))}</span>'
            f'<div class="cc-date">{esc(c.get("date"))}{resolved}</div></div>'
        )
    render('<div class="card-grid">' + "".join(parts) + "</div>")
    if len(records) > MAX_CARDS:
        st.caption(f"Showing the latest {MAX_CARDS} of {len(records)} complaints.")


def load_complaints():
    """Read all complaints (newest first) as plain dictionaries."""
    try:
        return [dict(row) for row in get_all_complaints()]
    except sqlite3.Error:
        st.error("The complaint database could not be read. Please try again shortly.")
        return []


def save_uploaded_image(uploaded_file):
    """Save the optional photo inside uploads/ and return its relative path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(uploaded_file.name))
    path = os.path.join(UPLOAD_DIR, f"{datetime.now():%Y%m%d_%H%M%S}_{safe_name}")
    with open(path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    return path


def show_flash():
    """Show (once) a message saved before a page refresh."""
    flash = st.session_state.get("flash")
    if flash:
        kind, message = flash
        (st.success if kind == "success" else st.info)(message)
        st.session_state.flash = None


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
def render_hero(complaints):
    total = len(complaints)
    resolved = sum(1 for c in complaints if c.get("status") == "Resolved")
    open_count = sum(1 for c in complaints if c.get("status") == "Open")
    render(f"""
    <div class="hero fade-in">
      <div class="hero-pill">AI-powered civic platform</div>
      <h1>AI Smart Civic Services</h1>
      <p class="hero-tagline">Report local problems. Track progress. Build better communities.</p>
      <p class="hero-desc">Citizens can report civic issues such as damaged roads, water leaks or broken streetlights.
      Our AI sorts every report into the right category, and the service team tracks it until it is resolved.</p>
      <div class="hero-stats">
        <div class="hero-stat"><span>{total}</span>Issues reported</div>
        <div class="hero-stat"><span>{open_count}</span>Waiting for action</div>
        <div class="hero-stat"><span>{resolved}</span>Resolved</div>
      </div>
    </div>
    """)


# ---------------------------------------------------------------------------
# Tab 1: Report an issue (citizen)
# ---------------------------------------------------------------------------
def clear_result():
    st.session_state.last_result = None


def handle_submission(description, location, image):
    """Validate, classify with AI, save. Returns True when the complaint was stored."""
    description = (description or "").strip()
    location = (location or "").strip()
    if not description:
        st.error("Please describe the problem before submitting.")
        return False
    if not location:
        st.error("Please enter the location of the problem.")
        return False

    notices = []

    # --- AI classification (the existing trained model) ---
    category = None
    if classify_complaint is None:
        notices.append("AI classification is currently unavailable, so this complaint was saved without a category.")
    else:
        try:
            category = classify_complaint(description)
        except Exception:
            notices.append("AI classification failed for this complaint, so it was saved without a category.")

    # --- Optional photo ---
    image_path = None
    if image is not None:
        try:
            image_path = save_uploaded_image(image)
        except OSError:
            notices.append("The photo could not be saved, but your complaint was submitted.")

    # --- Store in SQLite ---
    try:
        new_id = add_complaint(description, location, image_path, category)
        record = get_complaint_by_id(new_id)
    except sqlite3.Error:
        st.error("Sorry, your complaint could not be saved. Please try again.")
        return False

    record = dict(record) if record else {}
    st.session_state.last_result = {
        "id": new_id,
        "category": record.get("category", category),
        "status": record.get("status", "Open"),
        "location": record.get("location", location),
        "date": record.get("date", ""),
        "has_photo": image_path is not None,
        "notice": " ".join(notices),
    }
    st.session_state.form_version += 1  # gives the form fresh, empty fields
    return True


def show_last_result():
    result = st.session_state.last_result
    if not result:
        return
    if result["category"]:
        category_html = f'<span class="chip chip-ai">{esc(result["category"])}</span>'
    else:
        category_html = '<span class="chip chip-muted">Not classified</span>'
    notice_html = f'<div class="notice">{esc(result["notice"])}</div>' if result["notice"] else ""
    photo_html = "Attached" if result["has_photo"] else "None"
    render(f"""
    <div class="result-card fade-in">
      <div class="result-head">
        <div class="result-check">&#10003;</div>
        <div><div class="result-title">Complaint submitted</div>
        <div class="result-sub">Your report has been recorded. Keep your complaint ID for reference.</div></div>
      </div>
      <div class="result-grid">
        <div><div class="result-label">Complaint ID</div><div class="result-value">#{result["id"]}</div></div>
        <div><div class="result-label">AI classification</div>{category_html}</div>
        <div><div class="result-label">Status</div><span class="badge badge-{status_slug(result["status"])}">{esc(result["status"])}</span></div>
        <div><div class="result-label">Location</div><div class="result-value">{esc(result["location"])}</div></div>
        <div><div class="result-label">Submitted</div><div class="result-value">{esc(result["date"])}</div></div>
        <div><div class="result-label">Photo</div><div class="result-value">{photo_html}</div></div>
      </div>
      {notice_html}
    </div>
    """)
    st.button("Dismiss", key="dismiss_result", on_click=clear_result)


def render_report_tab():
    left, right = st.columns([3, 2], gap="large")

    with left:
        show_last_result()
        version = st.session_state.form_version  # changes after each success -> empty form
        with st.form("complaint_form"):
            st.markdown("#### Report a civic issue")
            st.caption("Describe the issue clearly so our AI can classify it accurately.")
            description = st.text_area(
                "What is the problem? *", key=f"description_{version}", height=130,
                placeholder="e.g. There is a large water leak near the main road and traffic is becoming difficult.",
            )
            location = st.text_input(
                "Location *", key=f"location_{version}",
                placeholder="e.g. Main Road, near City Park",
            )
            image = st.file_uploader(
                "Add a photo (optional)", type=["png", "jpg", "jpeg"], key=f"image_{version}",
            )
            st.caption("Photos are saved on the app server. On free hosting, saved files can be cleared when the app restarts.")
            submitted = st.form_submit_button("Submit complaint")
        if submitted and handle_submission(description, location, image):
            st.rerun()

    with right:
        chips = "".join(f'<span class="chip">{c}</span>' for c in VALID_CATEGORIES)
        render(f"""
        <div class="panel fade-in">
          <h4>How it works</h4>
          <div class="steps">
            <div class="step"><div class="step-num">1</div><b>Describe</b><span>Tell us what is wrong and where.</span></div>
            <div class="step"><div class="step-num">2</div><b>AI classifies</b><span>A trained model predicts the problem type.</span></div>
            <div class="step"><div class="step-num">3</div><b>Track</b><span>The service team updates the status.</span></div>
          </div>
        </div>
        <div class="panel fade-in">
          <h4>Tips for a clear report</h4>
          <ul>
            <li>Say exactly what is wrong (for example "streetlight not working").</li>
            <li>Mention a street name or landmark in the location.</li>
            <li>Add a photo if it is safe to take one.</li>
          </ul>
        </div>
        <div class="panel fade-in">
          <h4>Problem types our AI recognises</h4>
          {chips}
        </div>
        """)


# ---------------------------------------------------------------------------
# Tab 2: Manage complaints (administrator)
# ---------------------------------------------------------------------------
def render_manage_tab(complaints):
    show_flash()
    if not complaints:
        empty_state("No complaints yet", "Submitted complaints will appear here for the service team to manage.")
        return

    counts = Counter(c.get("status") for c in complaints)
    kpi_grid([
        ("Total complaints", len(complaints), "All time", ""),
        ("Open", counts.get("Open", 0), "Waiting for action", "open"),
        ("Assigned", counts.get("Assigned", 0), "Given to a team", "assigned"),
        ("In progress", counts.get("In Progress", 0), "Being worked on", "progress"),
        ("Resolved", counts.get("Resolved", 0), "Completed", "resolved"),
    ])

    list_col, update_col = st.columns([3, 2], gap="large")

    with list_col:
        render('<div class="section-title">Complaint records</div><div class="section-sub">Newest complaints first.</div>')
        limit = st.selectbox("Records to show", [10, 25, 50, 100], key="manage_limit")
        complaint_cards(complaints[:limit])

    with update_col:
        render('<div class="section-title">Update status</div><div class="section-sub">Move a complaint through the workflow.</div>')
        by_id = {c["complaint_id"]: c for c in complaints}
        selected_id = st.selectbox(
            "Select a complaint", list(by_id.keys()), key="manage_selected",
            format_func=lambda i: f"#{i} - {by_id[i].get('category') or 'Unclassified'} - {by_id[i].get('status')}",
        )
        selected = by_id[selected_id]
        current_status = selected.get("status") or "Open"

        render(f"""
        <div class="panel">
          <span class="badge badge-{status_slug(current_status)}">{esc(current_status)}</span>
          <span class="chip">{esc(selected.get("category") or "Unclassified")}</span>
          <p class="panel-text">{esc(selected.get("description"))}</p>
          <div class="cc-loc">{esc(selected.get("location"))}</div>
          <div class="cc-date">Submitted {esc(selected.get("date"))}</div>
        </div>
        """)

        photo = selected.get("image_path")
        if photo and os.path.exists(photo):
            st.image(photo, caption="Attached photo")

        start = VALID_STATUSES.index(current_status) if current_status in VALID_STATUSES else 0
        new_status = st.selectbox("New status", VALID_STATUSES, index=start, key=f"status_{selected_id}")
        if st.button("Update status", key=f"update_{selected_id}"):
            if new_status == current_status:
                st.info(f"Complaint #{selected_id} is already '{current_status}'.")
            else:
                try:
                    ok = update_status(selected_id, new_status)
                except sqlite3.Error:
                    ok = False
                if ok:
                    st.session_state.flash = ("success", f"Complaint #{selected_id} updated to '{new_status}'.")
                    st.rerun()
                else:
                    st.error("The status could not be updated. Please try again.")


# ---------------------------------------------------------------------------
# Tab 3: Search / filter
# ---------------------------------------------------------------------------
def render_search_tab():
    render('<div class="section-title">Find complaints</div><div class="section-sub">Filter by category and status, or search for a word in the description or location.</div>')
    col1, col2, col3 = st.columns([1, 1, 1.4])
    category = col1.selectbox("Category", ["Any"] + VALID_CATEGORIES, key="search_category")
    status = col2.selectbox("Status", ["Any"] + VALID_STATUSES, key="search_status")
    keyword = col3.text_input("Keyword (optional)", key="search_keyword", placeholder="e.g. streetlight, main road")

    try:
        rows = filter_complaints(None if category == "Any" else category,
                                 None if status == "Any" else status)
    except sqlite3.Error:
        st.error("The search could not be completed. Please try again.")
        return
    records = [dict(row) for row in rows]

    word = keyword.strip().lower()
    if word:
        records = [c for c in records
                   if word in str(c.get("description", "")).lower() or word in str(c.get("location", "")).lower()]

    render(f'<span class="count-pill">{len(records)} complaint(s) found</span>')
    if not records:
        empty_state("No matching complaints", "Try a different category, status or keyword.")
        return

    complaint_cards(records)
    with st.expander("View these results as a table"):
        table = pd.DataFrame(records)[["complaint_id", "date", "status", "category", "location", "description"]]
        st.dataframe(table, hide_index=True)


# ---------------------------------------------------------------------------
# Tab 4: Analytics
# ---------------------------------------------------------------------------
def category_chart(category_counts):
    names = list(VALID_CATEGORIES) + [c for c in category_counts if c not in VALID_CATEGORIES]
    data = pd.DataFrame({"Category": names, "Complaints": [category_counts.get(n, 0) for n in names]})
    base = alt.Chart(data).encode(
        y=alt.Y("Category:N", sort="-x", title=None, axis=alt.Axis(labelFontSize=13)),
        x=alt.X("Complaints:Q", title=None, axis=alt.Axis(tickMinStep=1)),
    )
    bars = base.mark_bar(color=ACCENT, cornerRadiusEnd=6, size=20).encode(tooltip=["Category", "Complaints"])
    labels = base.mark_text(align="left", dx=6, color=TEXT, fontWeight="bold").encode(text="Complaints:Q")
    return (bars + labels).properties(height=40 * len(names) + 20)


def status_chart(status_counts):
    data = pd.DataFrame(
        [{"Status": s, "Complaints": status_counts.get(s, 0)} for s in VALID_STATUSES if status_counts.get(s, 0) > 0]
    )
    return alt.Chart(data).mark_arc(innerRadius=62, outerRadius=108, stroke=CARD_BG, strokeWidth=2).encode(
        theta=alt.Theta("Complaints:Q"),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(domain=list(STATUS_COLORS.keys()), range=list(STATUS_COLORS.values())),
            legend=alt.Legend(orient="bottom", title=None),
        ),
        tooltip=["Status", "Complaints"],
    ).properties(height=320)


def trend_chart(complaints):
    dates = pd.to_datetime([c.get("date") for c in complaints], errors="coerce")
    daily = (pd.Series(dates).dropna().dt.normalize().value_counts().sort_index()
             .rename_axis("Day").reset_index(name="Complaints"))
    return alt.Chart(daily).mark_line(
        color=ACCENT, strokeWidth=3, point=alt.OverlayMarkDef(color="#06B6D4", size=90, filled=True)
    ).encode(
        x=alt.X("Day:T", title=None, axis=alt.Axis(format="%d %b")),
        y=alt.Y("Complaints:Q", title=None, axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip("Day:T", format="%d %b %Y"), "Complaints"],
    ).properties(height=260)


def resolution_histogram(hours_list):
    """Histogram of real resolution times, in the unit that reads best."""
    peak = max(hours_list)
    if peak < 1:
        unit, factor = "minutes", 60
    elif peak < 48:
        unit, factor = "hours", 1
    else:
        unit, factor = "days", 1 / 24
    data = pd.DataFrame({"Time": [h * factor for h in hours_list]})
    return alt.Chart(data).mark_bar(color=ACCENT, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Time:Q", bin=alt.Bin(maxbins=8), title=f"Time to resolve ({unit})"),
        y=alt.Y("count()", title="Complaints", axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip("count()", title="Complaints")],
    ).properties(height=280)


def render_resolution_section(hours_list):
    render('<div class="section-title">Resolution time</div><div class="section-sub">How long complaints take from submission to resolution.</div>')
    if not hours_list:
        empty_state("No resolved complaints yet",
                    "Resolution-time analytics will appear here once complaints are resolved.")
        return

    mean_val = statistics.mean(hours_list)
    median_val = statistics.median(hours_list)
    count = len(hours_list)

    chart_col, text_col = st.columns([3, 2], gap="large")
    with chart_col:
        show_chart(resolution_histogram(hours_list))
        st.caption("Each bar counts how many complaints were resolved within that time range.")
    with text_col:
        spread = ""
        if count > 1:
            spread = f" Times typically vary by about {friendly_time(statistics.stdev(hours_list))} around the average."
        small = " With so few resolved complaints, treat these numbers as a first impression." if count < 5 else ""
        render(f"""
        <div class="panel fade-in">
          <h4>What this means</h4>
          <p class="panel-text" style="margin:0;">
          Based on <b>{count}</b> resolved complaint(s), a complaint takes about <b>{friendly_time(mean_val)}</b> to resolve on average.
          Half of them were closed within <b>{friendly_time(median_val)}</b>.{esc(spread)}{esc(small)}</p>
        </div>
        """)

    cards = [
        ("Average (mean)", friendly_time(mean_val), "Total time divided by count", ""),
        ("Median", friendly_time(median_val), "The middle value", ""),
        ("Fastest", friendly_time(min(hours_list)), "Shortest resolution", "resolved"),
        ("Slowest", friendly_time(max(hours_list)), "Longest resolution", "open"),
    ]
    if count > 1:
        cards.append(("Std deviation", friendly_time(statistics.stdev(hours_list)), "How spread out the times are", ""))
        cards.append(("Variance", f"{statistics.variance(hours_list):.2f}", "In hours squared", ""))
    else:
        cards.append(("Std deviation", "-", "Needs 2+ resolved complaints", ""))
        cards.append(("Variance", "-", "Needs 2+ resolved complaints", ""))
    kpi_grid(cards)


def render_analytics_tab(complaints):
    if not complaints:
        empty_state("No complaints yet", "Analytics will appear here once citizens start reporting issues.")
        return
    try:
        status_counts = get_status_counts()
        category_counts = get_category_counts()
        hours_list = get_resolution_times()
    except sqlite3.Error:
        st.error("The statistics could not be calculated. Please try again.")
        return

    top = category_counts.most_common(1)
    top_name, top_count = top[0] if top else ("-", 0)
    avg_text = friendly_time(statistics.mean(hours_list)) if hours_list else "-"
    kpi_grid([
        ("Total complaints", len(complaints), "All time", ""),
        ("Open", status_counts.get("Open", 0), "Waiting for action", "open"),
        ("In progress", status_counts.get("In Progress", 0), "Being worked on", "progress"),
        ("Resolved", status_counts.get("Resolved", 0), "Completed", "resolved"),
        ("Most reported", top_name, f"{top_count} complaint(s)" if top else "", ""),
        ("Avg resolution time", avg_text, "From submission to resolved" if hours_list else "No resolved complaints yet", ""),
    ])

    left, right = st.columns(2, gap="large")
    with left:
        render('<div class="section-title">Complaints by category</div><div class="section-sub">Which problems are reported most often.</div>')
        show_chart(category_chart(category_counts))
    with right:
        render('<div class="section-title">Complaint status</div><div class="section-sub">Share of complaints at each stage.</div>')
        show_chart(status_chart(status_counts))

    render('<div class="section-title">Complaints over time</div><div class="section-sub">New complaints submitted per day.</div>')
    show_chart(trend_chart(complaints))

    render_resolution_section(hours_list)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    st.session_state.setdefault("form_version", 0)
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("flash", None)

    st.markdown(APP_CSS, unsafe_allow_html=True)

    try:
        init_db()
    except sqlite3.Error:
        st.error("The complaint database could not be started. Please reload the page.")
        st.stop()

    complaints = load_complaints()
    render_hero(complaints)

    if CLASSIFIER_ERROR:
        st.warning("The AI model could not be loaded. Complaints can still be submitted, but they will not be "
                   "classified automatically.")

    tab_report, tab_manage, tab_search, tab_analytics = st.tabs(
        ["📝 Report Issue", "📋 Manage", "🔍 Search", "📊 Analytics"]
    )
    with tab_report:
        render_report_tab()
    with tab_manage:
        render_manage_tab(complaints)
    with tab_search:
        render_search_tab()
    with tab_analytics:
        render_analytics_tab(complaints)

    st.caption("AI Smart Civic Services. Categories are predicted by a scikit-learn text classifier trained on a "
               "small dataset, so an occasional wrong prediction is possible.")


main()
