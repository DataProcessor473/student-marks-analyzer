import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import os
import re
import base64
import io
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Student Marks Analyzer Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# PWA support
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="theme-color" content="#4f46e5">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# Feature: API URL from Streamlit secrets (for cloud) or env (for local)
def _resolve_api_url() -> str:
    candidates = []
    try:
        if "API_URL" in st.secrets:
            candidates.append(str(st.secrets["API_URL"]).strip())
    except Exception:
        pass
    env_url = os.getenv("API_URL")
    if env_url:
        candidates.append(env_url.strip())
    FALLBACK = "https://student-marks-analyzer-vju7.onrender.com"
    candidates.append(FALLBACK)
    for url in candidates:
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            continue
        if "your-render" in url or "example.com" in url:
            continue
        is_cloud = bool(os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("IS_STREAMLIT_CLOUD"))
        if is_cloud and ("127.0.0.1" in url or "localhost" in url):
            continue
        return url.rstrip("/")
    return FALLBACK


API_URL = _resolve_api_url()

SESSION_TIMEOUT_MINUTES = 30

# ============================================================
# TRANSLATIONS
# ============================================================
TRANSLATIONS = {
    "en": {
        "dashboard": "🏠 Dashboard",
        "analyze": "📝 Analyze",
        "database": "📚 Database",
        "analytics": "📊 Analytics",
        "reports": "📈 Reports",
        "attendance": "📅 Attendance",
        "notifications": "🔔 Notifications",
        "compare": "🔄 Compare",
        "trends": "📉 Trends",
        "import_export": "📤 Import/Export",
        "bulk_import": "📥 Bulk Import",
        "users": "👥 Users",
        "audit": "📋 Audit Log",
        "classes": "🏫 Classes",
        "profile": "👤 Profile",
        "security": "🔒 Security",
        "settings": "⚙️ Settings",
        "parent_links": "👨‍👩‍👧 Parent Links",
        "my_children": "👨‍👩‍👧 My Children",
        "my_results": "📊 My Results",
        "my_progress": "📉 My Progress",
        "welcome": "Welcome",
        "logout": "🚪 Logout",
        "change_password": "🔑 Change Password",
        "exams": "📅 Exams",
        "timetable": "📆 Timetable",
        "assignments": "📝 Assignments",
        "fees": "💰 Fees",
        "backup": "💾 Backup",
        "scheduled_reports": "📧 Scheduled Reports",
        "filters": "🔍 Saved Filters",
        "live": "🔔 Live Feed",
        "pdf_templates": "📄 PDF Templates",
        "ml": "🤖 ML Insights",
    },
    "hi": {
        "dashboard": "🏠 डैशबोर्ड",
        "analyze": "📝 विश्लेषण",
        "database": "📚 डेटाबेस",
        "analytics": "📊 विश्लेषिकी",
        "reports": "📈 रिपोर्ट",
        "attendance": "📅 उपस्थिति",
        "notifications": "🔔 सूचनाएं",
        "compare": "🔄 तुलना",
        "trends": "📉 रुझान",
        "import_export": "📤 आयात/निर्यात",
        "bulk_import": "📥 थोक आयात",
        "users": "👥 उपयोगकर्ता",
        "audit": "📋 ऑडिट लॉग",
        "classes": "🏫 कक्षाएं",
        "profile": "👤 प्रोफ़ाइल",
        "security": "🔒 सुरक्षा",
        "settings": "⚙️ सेटिंग्स",
        "parent_links": "👨‍👩‍👧 अभिभावक लिंक",
        "my_children": "👨‍👩‍👧 मेरे बच्चे",
        "my_results": "📊 मेरे परिणाम",
        "my_progress": "📉 मेरी प्रगति",
        "welcome": "स्वागत है",
        "logout": "🚪 लॉग आउट",
        "change_password": "🔑 पासवर्ड बदलें",
        "exams": "📅 परीक्षा",
        "timetable": "📆 समय-सारणी",
        "assignments": "📝 असाइनमेंट",
        "fees": "💰 शुल्क",
        "backup": "💾 बैकअप",
        "scheduled_reports": "📧 निर्धारित रिपोर्ट",
        "filters": "🔍 सहेजे गए फ़िल्टर",
        "live": "🔔 लाइव फ़ीड",
        "pdf_templates": "📄 PDF टेम्पलेट",
        "ml": "🤖 एमएल अंतर्दृष्टि",
    },
}


def t(key):
    lang = st.session_state.get("language", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "theme": "light", "token": None, "refresh_token": None, "user": None,
    "logged_in": False, "analyze_result": None, "last_activity": None,
    "show_change_password": False, "show_verify_otp": False,
    "pending_verify_email": None, "pending_verify_phone": None,
    "reset_step": 1, "reset_identifier": None,
    "language": "en",
    "requires_2fa": False,
    "pending_2fa_username": None,
    "pending_2fa_password": None,
    "fa_qr": None,
    "fa_secret": None,
    "show_bulk_notif": False,
    "ws_messages": [],
    "bulk_import_preview": None,
    "show_add_student_form": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def apply_theme():
    """Apply theme CSS. Scoped, specific selectors only - no global wildcards."""
    import plotly.io as pio
    is_dark = st.session_state.get("theme", "light") == "dark"
    pio.templates.default = "plotly_dark" if is_dark else "plotly_white"

    # ---------- Theme palette ----------
    if is_dark:
        V = {
            "page_bg": "#0f1117",
            "surface": "#1a1d29",
            "surface_2": "#232736",
            "input_bg": "#1e2230",
            "border": "#2a2f42",
            "border_soft": "#20243a",
            "text": "#e8eaf2",
            "text_muted": "#9aa0b4",
            "text_dim": "#6c7288",
            "primary": "#6366f1",
            "primary_hover": "#818cf8",
            "primary_soft": "rgba(99,102,241,0.14)",
            "accent": "#8b5cf6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "sidebar_bg": "#12141d",
            "sidebar_border": "#20243a",
            "sidebar_text": "#c9cdda",
            "sidebar_text_dim": "#7d8399",
            "sidebar_hover": "rgba(99,102,241,0.12)",
            "sidebar_selected_bg": "rgba(99,102,241,0.18)",
            "header_bg": "linear-gradient(135deg, #1e2230 0%, #232736 100%)",
            "shadow": "0 4px 20px rgba(0,0,0,0.35)",
            "shadow_soft": "0 1px 3px rgba(0,0,0,0.25)",
        }
    else:
        V = {
            "page_bg": "#f8fafc",
            "surface": "#ffffff",
            "surface_2": "#f1f5f9",
            "input_bg": "#ffffff",
            "border": "#e2e8f0",
            "border_soft": "#eef2f7",
            "text": "#0f172a",
            "text_muted": "#64748b",
            "text_dim": "#94a3b8",
            "primary": "#4f46e5",
            "primary_hover": "#6366f1",
            "primary_soft": "rgba(79,70,229,0.08)",
            "accent": "#7c3aed",
            "success": "#059669",
            "warning": "#d97706",
            "danger": "#dc2626",
            "sidebar_bg": "#ffffff",
            "sidebar_border": "#e2e8f0",
            "sidebar_text": "#334155",
            "sidebar_text_dim": "#94a3b8",
            "sidebar_hover": "rgba(79,70,229,0.06)",
            "sidebar_selected_bg": "rgba(79,70,229,0.10)",
            "header_bg": "linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)",
            "shadow": "0 4px 20px rgba(15,23,42,0.06)",
            "shadow_soft": "0 1px 3px rgba(15,23,42,0.05)",
        }

    st.markdown(f"""
    <style>
    /* ============ FONTS ============ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ============ APP BACKGROUND ============ */
    .stApp {{
        background-color: {V["page_bg"]};
        color: {V["text"]};
    }}
    .main .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }}
    [data-testid="stHeader"] {{
        background-color: transparent;
    }}
    [data-testid="stToolbar"] {{
        right: 1rem;
    }}

    /* ============ TYPOGRAPHY ============ */
    h1, h2, h3, h4, h5, h6 {{
        color: {V["text"]};
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    h1 {{ font-size: 1.9rem; }}
    h2 {{ font-size: 1.5rem; }}
    h3 {{ font-size: 1.2rem; }}
    p, span, label, li {{
        color: {V["text"]};
    }}
    .stMarkdown p {{
        color: {V["text"]};
    }}
    small {{
        color: {V["text_muted"]};
    }}
    a, a:visited {{
        color: {V["primary"]};
        text-decoration: none;
    }}
    a:hover {{
        color: {V["primary_hover"]};
        text-decoration: underline;
    }}

    /* ============ HEADER ============ */
    .main-header {{
        background: {V["surface"]};
        border: 1px solid {V["border"]};
        padding: 1.75rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: {V["shadow_soft"]};
    }}
    .main-header h1 {{
        color: {V["text"]} !important;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.03em;
    }}
    .main-header p {{
        color: {V["text_muted"]} !important;
        margin: 0.35rem 0 0 0;
        font-size: 0.95rem;
    }}

    /* ============ METRIC CARDS ============ */
    .metric-card {{
        background: {V["surface"]};
        border: 1px solid {V["border"]};
        padding: 1.25rem 1.4rem;
        border-radius: 14px;
        box-shadow: {V["shadow_soft"]};
        transition: all 0.15s ease;
        height: 100%;
    }}
    .metric-card:hover {{
        border-color: {V["primary"]};
        box-shadow: {V["shadow"]};
        transform: translateY(-1px);
    }}
    .metric-card .metric-icon {{
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        line-height: 1;
    }}
    .metric-card .metric-value {{
        color: {V["text"]};
        font-size: 1.7rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
    }}
    .metric-card .metric-label {{
        color: {V["text_muted"]};
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    /* ============ RECOMMENDATION / INFO CARDS ============ */
    .recommendation-card {{
        background: {V["primary_soft"]};
        border-left: 3px solid {V["primary"]};
        padding: 0.85rem 1.15rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: {V["text"]};
        font-size: 0.9rem;
    }}
    .info-banner {{
        background: {V["primary_soft"]};
        border-left: 3px solid {V["primary"]};
        padding: 0.85rem 1.15rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: {V["text"]};
    }}

    /* ============ BADGES ============ */
    .password-strength-bar {{
        height: 6px;
        border-radius: 3px;
        margin: 0.4rem 0;
        overflow: hidden;
    }}
    .role-badge {{
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    /* ============ SIDEBAR ============ */
    section[data-testid="stSidebar"] {{
        background-color: {V["sidebar_bg"]};
        border-right: 1px solid {V["sidebar_border"]};
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 1rem;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {V["sidebar_text"]} !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span {{
        color: {V["sidebar_text"]};
    }}
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {{
        color: {V["sidebar_text_dim"]} !important;
    }}

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {{
        background-color: transparent !important;
        border: 1px solid {V["sidebar_border"]} !important;
        color: {V["sidebar_text"]} !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background-color: {V["sidebar_hover"]} !important;
        border-color: {V["primary"]} !important;
        color: {V["primary"]} !important;
    }}

    /* Sidebar radio (custom nav) */
    section[data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 0.15rem;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {{
        background-color: transparent;
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        border-left: 3px solid transparent;
        transition: all 0.15s ease;
        cursor: pointer;
        margin: 0;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
        background-color: {V["sidebar_hover"]};
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
        background-color: {V["sidebar_selected_bg"]};
        border-left-color: {V["primary"]};
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] > label p {{
        color: {V["sidebar_text"]};
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0;
    }}

    /* Sidebar selectbox / toggle */
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stToggle label {{
        color: {V["sidebar_text_dim"]} !important;
        font-size: 0.8rem !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {{
        background-color: {V["surface_2"]} !important;
        border-color: {V["sidebar_border"]} !important;
        color: {V["sidebar_text"]} !important;
    }}

    /* ============ INPUTS ============ */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stDateInput input,
    .stTimeInput input {{
        background-color: {V["input_bg"]} !important;
        color: {V["text"]} !important;
        border: 1px solid {V["border"]} !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus,
    .stDateInput input:focus {{
        border-color: {V["primary"]} !important;
        box-shadow: 0 0 0 3px {V["primary_soft"]} !important;
    }}
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {{
        color: {V["text_dim"]} !important;
    }}

    /* Labels */
    .stTextInput label,
    .stNumberInput label,
    .stTextArea label,
    .stDateInput label,
    .stTimeInput label,
    .stSelectbox label,
    .stMultiSelect label,
    .stSlider label,
    .stFileUploader label {{
        color: {V["text"]} !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }}

    /* ============ SELECT / MULTISELECT ============ */
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {{
        background-color: {V["input_bg"]} !important;
        border-color: {V["border"]} !important;
        border-radius: 8px !important;
        color: {V["text"]} !important;
        font-size: 0.9rem !important;
    }}
    .stSelectbox [data-baseweb="select"] svg,
    .stMultiSelect [data-baseweb="select"] svg {{
        fill: {V["text_muted"]} !important;
    }}
    [data-baseweb="popover"] {{
        background-color: {V["surface"]} !important;
        border: 1px solid {V["border"]} !important;
        border-radius: 10px !important;
        box-shadow: {V["shadow"]} !important;
    }}
    [role="listbox"] {{
        background-color: {V["surface"]} !important;
    }}
    [role="option"] {{
        color: {V["text"]} !important;
        font-size: 0.88rem !important;
    }}
    [role="option"]:hover,
    [role="option"][aria-selected="true"] {{
        background-color: {V["primary_soft"]} !important;
        color: {V["primary"]} !important;
    }}

    /* ============ BUTTONS ============ */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {{
        background-color: {V["primary"]} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.5rem 1rem !important;
        transition: background-color 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {{
        background-color: {V["primary_hover"]} !important;
        box-shadow: 0 4px 12px {V["primary_soft"]} !important;
    }}
    .stButton > button:active {{
        transform: translateY(1px);
    }}
    .stButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {{
        background-color: {V["surface"]} !important;
        color: {V["text"]} !important;
        border: 1px solid {V["border"]} !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background-color: {V["surface_2"]} !important;
        border-color: {V["primary"]} !important;
        color: {V["primary"]} !important;
    }}

    /* ============ TABS ============ */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        background-color: transparent;
        border-bottom: 1px solid {V["border"]};
        padding-bottom: 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent;
        color: {V["text_muted"]};
        border-radius: 8px 8px 0 0;
        padding: 0.6rem 1rem;
        font-weight: 500;
        font-size: 0.88rem;
        border-bottom: 2px solid transparent;
        transition: all 0.15s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {V["text"]};
        background-color: {V["surface_2"]};
    }}
    .stTabs [aria-selected="true"] {{
        color: {V["primary"]} !important;
        border-bottom-color: {V["primary"]} !important;
        font-weight: 600;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {V["primary"]};
    }}

    /* ============ EXPANDER ============ */
    [data-testid="stExpander"] {{
        background-color: {V["surface"]};
        border: 1px solid {V["border"]};
        border-radius: 10px;
        overflow: hidden;
        box-shadow: {V["shadow_soft"]};
    }}
    [data-testid="stExpander"] summary {{
        background-color: {V["surface"]};
        color: {V["text"]};
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.75rem 1rem;
    }}
    [data-testid="stExpander"] summary:hover {{
        background-color: {V["surface_2"]};
    }}
    [data-testid="stExpander"] summary p {{
        color: {V["text"]} !important;
    }}

    /* ============ DATAFRAMES ============ */
    [data-testid="stDataFrame"] {{
        border: 1px solid {V["border"]};
        border-radius: 10px;
        overflow: hidden;
        background-color: {V["surface"]};
    }}
    [data-testid="stDataFrame"] [role="columnheader"] {{
        background-color: {V["surface_2"]} !important;
        color: {V["text"]} !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        border-bottom: 1px solid {V["border"]} !important;
    }}
    [data-testid="stDataFrame"] [role="gridcell"] {{
        color: {V["text"]} !important;
        background-color: {V["surface"]} !important;
        font-size: 0.85rem !important;
    }}
    [data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {{
        background-color: {V["surface_2"]} !important;
    }}

    /* ============ METRICS ============ */
    [data-testid="stMetric"] {{
        background-color: {V["surface"]};
        padding: 0.85rem 1rem;
        border-radius: 12px;
        border: 1px solid {V["border"]};
        box-shadow: {V["shadow_soft"]};
    }}
    [data-testid="stMetricValue"] {{
        color: {V["text"]} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {V["text_muted"]} !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    [data-testid="stMetricDelta"] {{
        font-size: 0.8rem !important;
    }}

    /* ============ ALERTS ============ */
    [data-testid="stAlert"] {{
        border-radius: 10px;
        border: 1px solid {V["border"]};
        background-color: {V["surface"]};
        padding: 0.85rem 1rem;
    }}
    [data-testid="stAlert"] p {{
        color: {V["text"]} !important;
        font-size: 0.88rem;
        margin: 0;
    }}

    /* ============ FILE UPLOADER ============ */
    [data-testid="stFileUploader"] {{
        background-color: {V["surface"]};
        border: 1px solid {V["border"]};
        border-radius: 12px;
        padding: 0.5rem;
    }}
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploadDropzone"] {{
        background-color: {V["surface_2"]};
        border: 2px dashed {V["border"]};
        border-radius: 10px;
        transition: border-color 0.15s ease;
    }}
    [data-testid="stFileUploadDropzone"]:hover {{
        border-color: {V["primary"]};
        background-color: {V["primary_soft"]};
    }}
    [data-testid="stFileUploadDropzone"] span,
    [data-testid="stFileUploadDropzone"] small {{
        color: {V["text_muted"]} !important;
    }}
    [data-testid="stFileUploadDropzone"] button {{
        background-color: {V["primary"]} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}

    /* ============ RADIO / CHECKBOX ============ */
    .stRadio > div {{
        gap: 0.5rem;
    }}
    .stRadio label,
    .stCheckbox label {{
        color: {V["text"]} !important;
        font-size: 0.88rem !important;
    }}

    /* ============ PROGRESS ============ */
    .stProgress > div > div {{
        background-color: {V["surface_2"]};
        border-radius: 4px;
    }}
    .stProgress > div > div > div {{
        background-color: {V["primary"]};
        border-radius: 4px;
    }}

    /* ============ CHARTS ============ */
    .js-plotly-plot,
    .plot-container {{
        background-color: transparent !important;
    }}
    .js-plotly-plot .plotly .main-svg {{
        background-color: transparent !important;
    }}

    /* ============ DIVIDERS ============ */
    hr {{
        border: none;
        border-top: 1px solid {V["border"]};
        margin: 1.25rem 0;
    }}

    /* ============ SCROLLBAR ============ */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {V["border"]};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {V["text_dim"]};
    }}

    /* ============ CODE / JSON ============ */
    code {{
        background-color: {V["surface_2"]} !important;
        color: {V["primary"]} !important;
        border-radius: 6px !important;
        padding: 0.1rem 0.35rem !important;
        font-size: 0.85rem !important;
    }}
    pre {{
        background-color: {V["surface_2"]} !important;
        border: 1px solid {V["border"]} !important;
        border-radius: 10px !important;
    }}
    pre code {{
        color: {V["text"]} !important;
        background-color: transparent !important;
    }}

    /* ============ MODAL / TOAST ============ */
    [data-testid="stModal"] {{
        background-color: {V["surface"]} !important;
        border: 1px solid {V["border"]} !important;
        border-radius: 14px !important;
    }}
    [data-testid="stToast"] {{
        background-color: {V["surface"]} !important;
        color: {V["text"]} !important;
        border: 1px solid {V["border"]} !important;
        border-radius: 10px !important;
    }}

    /* ============ FORM ============ */
    [data-testid="stForm"] {{
        background-color: {V["surface"]};
        border: 1px solid {V["border"]};
        border-radius: 14px;
        padding: 1.25rem;
        box-shadow: {V["shadow_soft"]};
    }}

    /* ============ MOBILE RESPONSIVE ============ */
    @media (max-width: 768px) {{
        .main-header {{
            padding: 1.25rem 1rem !important;
        }}
        .main-header h1 {{
            font-size: 1.4rem !important;
        }}
        .metric-card {{
            padding: 1rem !important;
        }}
        .metric-card .metric-value {{
            font-size: 1.35rem !important;
        }}
        .main .block-container {{
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }}
    }}
    @media (hover: none) {{
        .stButton > button {{
            min-height: 44px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


apply_theme()


# ============================================================
# CHART THEME HELPERS (theme-aware colors for Plotly)
# ============================================================
def get_chart_colors() -> dict:
    """Return theme-aware colors for charts."""
    is_dark = st.session_state.get("theme", "light") == "dark"
    if is_dark:
        return {
            "bg": "#1a1d29",
            "paper": "#1a1d29",
            "text": "#e8eaf2",
            "grid": "#2a2f42",
            "zeroline": "#3a4055",
            "primary": "#6366f1",
            "accent": "#8b5cf6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "muted": "#9aa0b4",
            "gradient_good": "#10b981",
            "gradient_mid": "#f59e0b",
            "gradient_bad": "#ef4444",
            "grade_colors": {
                "A+": "#10b981", "A": "#34d399", "B": "#84cc16",
                "C": "#fbbf24", "D": "#f59e0b", "E": "#f97316", "F": "#ef4444",
            },
        }
    return {
        "bg": "#ffffff",
        "paper": "#ffffff",
        "text": "#0f172a",
        "grid": "#e2e8f0",
        "zeroline": "#cbd5e1",
        "primary": "#4f46e5",
        "accent": "#7c3aed",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "muted": "#64748b",
        "gradient_good": "#10b981",
        "gradient_mid": "#fbbf24",
        "gradient_bad": "#ef4444",
        "grade_colors": {
            "A+": "#10b981", "A": "#34d399", "B": "#84cc16",
            "C": "#fbbf24", "D": "#f59e0b", "E": "#f97316", "F": "#dc2626",
        },
    }


def style_chart(fig):
    """Apply theme-aware styling to a Plotly figure. Returns the figure."""
    c = get_chart_colors()
    fig.update_layout(
        paper_bgcolor=c["paper"],
        plot_bgcolor=c["bg"],
        font=dict(color=c["text"], family="Inter, sans-serif", size=12),
        title_font=dict(color=c["text"], size=14),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=c["grid"],
            font=dict(color=c["text"]),
        ),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    # Style axes if present
    fig.update_xaxes(
        gridcolor=c["grid"],
        zerolinecolor=c["zeroline"],
        tickfont=dict(color=c["text"]),
        title_font=dict(color=c["text"]),
    )
    fig.update_yaxes(
        gridcolor=c["grid"],
        zerolinecolor=c["zeroline"],
        tickfont=dict(color=c["text"]),
        title_font=dict(color=c["text"]),
    )
    return fig



def get_auth_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def handle_response(resp, show_error=True):
    if resp is None:
        return None
    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return {}
    elif resp.status_code == 401:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.user = None
        st.error("🔒 Session expired. Please log in again.")
        st.rerun()
    elif resp.status_code == 403:
        if show_error:
            try:
                st.error(f"🚫 {resp.json().get('detail', 'Access denied')}")
            except Exception:
                st.error("🚫 Access denied")
    elif resp.status_code == 404:
        if show_error:
            st.error("❓ Resource not found")
    elif resp.status_code == 423:
        if show_error:
            try:
                st.error(f"🔒 {resp.json().get('detail', 'Account locked')}")
            except Exception:
                st.error("🔒 Account locked")
    elif resp.status_code == 429:
        st.warning("⏱️ Too many requests. Please wait.")
    else:
        if show_error:
            try:
                st.error(f"❌ Error: {resp.json().get('detail', resp.text)}")
            except Exception:
                st.error(f"❌ Error: {resp.text}")
    return None


def api_get(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=90, **kwargs)
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def api_post(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.post(f"{API_URL}{endpoint}", headers=headers, timeout=90, **kwargs)
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def api_put(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.put(f"{API_URL}{endpoint}", headers=headers, timeout=90, **kwargs)
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def api_delete(endpoint, **kwargs):
    try:
        headers = kwargs.pop("headers", {})
        headers.update(get_auth_headers())
        return requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=90, **kwargs)
    except Exception as e:
        st.error(f"❌ Network error: {e}")
        return None


def password_strength_meter(password):
    if not password:
        return
    score = 0
    if len(password) >= 8: score += 20
    if len(password) >= 12: score += 10
    if re.search(r"[A-Z]", password): score += 15
    if re.search(r"[a-z]", password): score += 15
    if re.search(r"\d", password): score += 15
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]", password): score += 15
    if len(set(password)) > 6: score += 10
    score = min(score, 100)
    if score < 40:
        color, label = "#ef4444", "Weak"
    elif score < 60:
        color, label = "#f59e0b", "Fair"
    elif score < 80:
        color, label = "#3b82f6", "Good"
    else:
        color, label = "#10b981", "Strong"
    st.markdown(f"""
        <div style="margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                <span>Password Strength</span>
                <span style="color: {color}; font-weight: 600;">{label}</span>
            </div>
            <div class="password-strength-bar" style="background: #e5e7eb;">
                <div style="height: 100%; width: {score}%; background: {color}; border-radius: 4px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def get_role_badge(role):
    colors = {
        "admin": ("#dc2626", "👑 Admin"),
        "teacher": ("#2563eb", "👨‍🏫 Teacher"),
        "student": ("#10b981", "🎓 Student"),
        "parent": ("#8b5cf6", "👨‍👩‍👧 Parent"),
    }
    bg, label = colors.get(role, ("#6b7280", role))
    return f'<span class="role-badge" style="background: {bg}; color: white;">{label}</span>'


def render_metric(icon, value, label):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)


def get_student_photo_url(photo_url):
    if not photo_url:
        return None
    if photo_url.startswith("http"):
        return photo_url
    return f"{API_URL}{photo_url}"


# ============================================================
# LOGIN / REGISTER / FORGOT / 2FA
# ============================================================
if not st.session_state.logged_in:
    st.markdown(f"""
        <div class="main-header" style="text-align: center;">
            <h1>🎓 Student Marks Analyzer Pro</h1>
            <p>Secure Edition v12.0.0</p>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("requires_2fa"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Two-Factor Authentication")
            st.info("Enter the 6-digit code from your authenticator app")
            with st.form("2fa_form"):
                code = st.text_input("2FA Code", max_chars=6, placeholder="123456")
                if st.form_submit_button("Verify", use_container_width=True):
                    if len(code) == 6:
                        r = requests.post(f"{API_URL}/auth/login", params={
                            "username": st.session_state.pending_2fa_username,
                            "password": st.session_state.pending_2fa_password,
                            "totp_code": code,
                        })
                        if r.status_code == 200:
                            d = r.json()
                            st.session_state.token = d["access_token"]
                            st.session_state.refresh_token = d.get("refresh_token")
                            st.session_state.user = d["user"]
                            st.session_state.language = d["user"].get("language", "en")
                            st.session_state.theme = d["user"].get("theme", "light")
                            st.session_state.logged_in = True
                            st.session_state.last_activity = datetime.now()
                            st.session_state.requires_2fa = False
                            st.session_state.pending_2fa_username = None
                            st.session_state.pending_2fa_password = None
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Invalid 2FA code"))
                    else:
                        st.warning("Enter a 6-digit code")
            if st.button("← Back to Login"):
                st.session_state.requires_2fa = False
                st.rerun()
        st.stop()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register, tab_forgot = st.tabs(["🔐 Login", "📝 Register", "🔑 Forgot Password"])

        with tab_login:
            st.markdown("### Welcome Back")
            st.caption("Sign in with your username OR email")
            with st.form("login_form"):
                identifier = st.text_input("Username or Email", placeholder="admin or admin@example.com")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("🚀 Login", use_container_width=True):
                    if not identifier or not password:
                        st.warning("⚠️ Please enter both fields")
                    else:
                        with st.spinner("Authenticating..."):
                            try:
                                r = requests.post(
                                    f"{API_URL}/auth/login",
                                    params={"username": identifier.strip(), "password": password},
                                    timeout=90,
                                )
                                if r.status_code == 200:
                                    d = r.json()
                                    if d.get("requires_2fa"):
                                        st.session_state.requires_2fa = True
                                        st.session_state.pending_2fa_username = identifier.strip()
                                        st.session_state.pending_2fa_password = password
                                        st.rerun()
                                    else:
                                        st.session_state.token = d["access_token"]
                                        st.session_state.refresh_token = d.get("refresh_token")
                                        st.session_state.user = d["user"]
                                        st.session_state.language = d["user"].get("language", "en")
                                        st.session_state.theme = d["user"].get("theme", "light")
                                        st.session_state.logged_in = True
                                        st.session_state.last_activity = datetime.now()
                                        st.rerun()
                                elif r.status_code == 423:
                                    st.error("🔒 " + r.json().get("detail", "Account locked"))
                                elif r.status_code == 403:
                                    st.error("🚫 " + r.json().get("detail", "Account disabled"))
                                elif r.status_code == 401:
                                    st.error("❌ Invalid username/email or password")
                                elif r.status_code == 404:
                                    st.error(f"❌ Endpoint not found: {API_URL}/auth/login")
                                elif r.status_code == 429:
                                    st.warning("⏱️ Too many attempts. Wait a minute.")
                                else:
                                    st.error(f"❌ Error: {r.text[:200]}")
                            except Exception as e:
                                st.error(f"❌ {str(e)}")

            st.info("""
            **🔐 Default Credentials**
            - Primary: `admin` / `Admin@123`
            - Backup: `admin2` / `Admin2@123`
            """)

        with tab_register:
            st.markdown("### Create Account")
            reg_role = st.selectbox("I am a...", ["teacher", "student", "parent"], key="reg_role_select")
            with st.form("register_form"):
                new_username = st.text_input("👤 Username *", placeholder="johndoe")
                new_email = st.text_input("📧 Email *", placeholder="john@example.com")
                new_phone = st.text_input("📱 Phone (optional)", placeholder="+919876543210")
                new_fullname = st.text_input("📝 Full Name")
                col_a, col_b = st.columns(2)
                with col_a:
                    new_password = st.text_input("🔑 Password *", type="password")
                with col_b:
                    confirm_password = st.text_input("🔑 Confirm *", type="password")
                if new_password:
                    password_strength_meter(new_password)
                if st.form_submit_button("📝 Create Account", use_container_width=True):
                    errors = []
                    if not new_username or len(new_username) < 3:
                        errors.append("Username must be 3+ chars")
                    elif not re.match(r"^[a-zA-Z0-9_]+$", new_username):
                        errors.append("Username: letters/numbers/underscores only")
                    if not new_email or "@" not in new_email:
                        errors.append("Valid email required")
                    if not new_password or len(new_password) < 8:
                        errors.append("Password must be 8+ chars")
                    elif new_password != confirm_password:
                        errors.append("Passwords don't match")
                    if errors:
                        for e in errors:
                            st.error(f"❌ {e}")
                    else:
                        with st.spinner("Creating account..."):
                            try:
                                payload = {
                                    "username": new_username.lower().strip(),
                                    "email": new_email.strip(),
                                    "phone": new_phone.strip() or None,
                                    "password": new_password,
                                    "full_name": new_fullname or new_username,
                                    "role": reg_role,
                                }
                                r = requests.post(f"{API_URL}/auth/register", json=payload, timeout=90)
                                if r.status_code == 200:
                                    d = r.json()
                                    st.session_state.pending_verify_email = d["email"]
                                    st.session_state.show_verify_otp = True
                                    st.success(d["message"])
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(r.json().get("detail", "Registration failed"))
                            except Exception as e:
                                st.error(f"❌ {e}")

            if st.session_state.get("show_verify_otp") and st.session_state.get("pending_verify_email"):
                st.markdown("---")
                st.markdown("### 🔐 Verify Your Account")
                st.info(f"OTP sent to **{st.session_state.pending_verify_email}**")
                email_otp = st.text_input("Enter OTP", key="email_otp_input", max_chars=6)
                if st.button("✅ Verify", key="verify_email_btn", use_container_width=True):
                    if email_otp:
                        try:
                            r = requests.post(f"{API_URL}/auth/verify-otp", json={
                                "identifier": st.session_state.pending_verify_email,
                                "otp_code": email_otp.strip(),
                                "purpose": "verification",
                            }, timeout=90)
                            if r.status_code == 200:
                                st.success("✅ Verified! You can log in now.")
                                st.session_state.show_verify_otp = False
                                st.session_state.pending_verify_email = None
                            else:
                                st.error(r.json().get("detail", "Invalid OTP"))
                        except Exception as e:
                            st.error(f"Error: {e}")

        with tab_forgot:
            st.markdown("### Reset Password")
            if st.session_state.reset_step == 1:
                reset_id = st.text_input("Email or Phone", placeholder="you@example.com")
                if st.button("📧 Send OTP", use_container_width=True, key="send_reset_otp"):
                    if not reset_id:
                        st.warning("Enter email or phone")
                    else:
                        try:
                            r = requests.post(f"{API_URL}/auth/send-otp",
                                            json={"identifier": reset_id.strip(),
                                                  "purpose": "reset_password"},
                                            timeout=90)
                            if r.status_code == 200:
                                st.session_state.reset_identifier = reset_id.strip()
                                st.session_state.reset_step = 2
                                st.success("OTP sent")
                                st.rerun()
                            else:
                                st.error(r.json().get("detail", "Failed"))
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.info(f"OTP sent to {st.session_state.reset_identifier}")
                otp_code = st.text_input("OTP", max_chars=6)
                new_pw = st.text_input("New Password", type="password")
                if new_pw:
                    password_strength_meter(new_pw)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Reset", use_container_width=True):
                        if otp_code and new_pw and len(new_pw) >= 8:
                            try:
                                r = requests.post(f"{API_URL}/auth/reset-password", json={
                                    "identifier": st.session_state.reset_identifier,
                                    "otp_code": otp_code.strip(),
                                    "new_password": new_pw,
                                }, timeout=90)
                                if r.status_code == 200:
                                    st.success("Password reset! Log in now.")
                                    st.session_state.reset_step = 1
                                    st.rerun()
                                else:
                                    st.error(r.json().get("detail", "Failed"))
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.warning("Fill all fields (8+ chars)")
                with c2:
                    if st.button("Back", use_container_width=True):
                        st.session_state.reset_step = 1
                        st.rerun()

    st.stop()


# Session timeout
if st.session_state.last_activity:
    elapsed = (datetime.now() - st.session_state.last_activity).total_seconds() / 60
    if elapsed > SESSION_TIMEOUT_MINUTES:
        st.warning("Session expired")
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.user = None
        time.sleep(1)
        st.rerun()
st.session_state.last_activity = datetime.now()


# Change password page
if st.session_state.show_change_password:
    st.markdown(f'<div class="main-header"><h1>{t("change_password")}</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("cp_form"):
            op = st.text_input("Current Password", type="password")
            np_ = st.text_input("New Password", type="password")
            cp = st.text_input("Confirm Password", type="password")
            if np_:
                password_strength_meter(np_)
            cc1, cc2 = st.columns(2)
            with cc1:
                save = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
            with cc2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
            if save:
                if not op or not np_ or not cp:
                    st.error("Fill all fields")
                elif np_ != cp:
                    st.error("Passwords don't match")
                elif len(np_) < 8:
                    st.error("Password must be 8+ chars")
                else:
                    r = api_post("/auth/change-password",
                                 json={"old_password": op, "new_password": np_})
                    if r and r.status_code == 200:
                        st.success("✅ Changed!")
                        time.sleep(1)
                        st.session_state.show_change_password = False
                        st.rerun()
                    elif r and r.status_code == 400:
                        st.error(r.json().get("detail", "Error"))
            if cancel:
                st.session_state.show_change_password = False
                st.rerun()
    st.stop()


# User info
user = st.session_state.user
user_role = user.get("role", "teacher")
user_name = user.get("full_name") or user["username"]

if "language" not in st.session_state or not st.session_state.language:
    st.session_state.language = user.get("language", "en")


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
            <h2 style="color: inherit; margin: 0; font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em;">🎓 Pro Analyzer</h2>
            <p style="color: #94a3b8; font-size: 0.72rem; margin: 0.25rem 0 0 0;">v12.0.0</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.15); padding: 0.75rem 0.85rem; border-radius: 10px; margin-bottom: 1rem;">
            <p style="color: inherit; margin: 0; font-weight: 600; font-size: 0.88rem;">👤 {user_name}</p>
            <p style="color: #94a3b8; margin: 0.15rem 0 0 0; font-size: 0.75rem;">@{user['username']}</p>
            <div style="margin-top: 0.5rem;">{get_role_badge(user_role)}</div>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown("**🌙 Dark Mode**")
    with col_b:
        is_dark = st.session_state.theme == "dark"
        toggled = st.toggle("d", value=is_dark, key="theme_toggle", label_visibility="collapsed")
        if toggled != is_dark:
            new_theme = "dark" if toggled else "light"
            st.session_state.theme = new_theme
            api_put("/auth/theme", json={"theme": new_theme})
            st.rerun()

    lang_choice = st.selectbox(
        "🌍 Language",
        ["en", "hi"],
        format_func=lambda x: "English" if x == "en" else "हिन्दी",
        index=0 if st.session_state.language == "en" else 1,
        key="lang_select",
    )
    if lang_choice != st.session_state.language:
        st.session_state.language = lang_choice
        api_put("/auth/language", json={"language": lang_choice})
        st.rerun()



    # ============================================================
    # QUICK SEARCH (Feature 21)
    # ============================================================
    if user_role in ("admin", "teacher"):
        with st.expander("Quick Search", expanded=False):
            _qs_query = st.text_input(
                "Search students",
                placeholder="Type a name...",
                key="quick_search_q",
                label_visibility="collapsed",
            )
            if _qs_query and len(_qs_query.strip()) >= 2:
                try:
                    _qs_resp = api_get("/students", params={"limit": 500})
                    _qs_data = handle_response(_qs_resp, show_error=False) if _qs_resp else None
                    _qs_students = _qs_data.get("students", []) if _qs_data else []
                    _qs_matches = [
                        s for s in _qs_students
                        if _qs_query.strip().lower() in s.get("name", "").lower()
                    ][:6]
                    if not _qs_matches:
                        st.caption("No matches")
                    else:
                        for _m in _qs_matches:
                            _label = _m["name"] + " - " + (_m.get("class_name") or "N/A")
                            if st.button(_label, key="qs_" + str(_m["id"]), use_container_width=True):
                                st.session_state["_qs_goto_student_id"] = _m["id"]
                                st.session_state["_qs_goto_student_name"] = _m["name"]
                                st.info("Student ID " + str(_m["id"]) + " saved. Go to Profile page to view.")
                except Exception as _e:
                    st.caption("Search error: " + str(_e))

    st.markdown("---")
    st.markdown("---")

    # Build menu based on role
    if user_role == "admin":
        menu_options = [
            t("dashboard"), t("analyze"), t("database"), t("analytics"),
            t("reports"), t("attendance"), t("exams"), t("timetable"),
            t("assignments"), t("fees"), t("classes"), t("parent_links"),
            "🏫 Class Assignments",
            "⚙️ Grade Schemes",
            t("profile"), t("filters"), t("live"), t("notifications"),
            t("scheduled_reports"), t("backup"), t("pdf_templates"),
            t("users"), t("audit"), t("settings"), t("ml"), t("bulk_import"),
        ]
        menu_icons = [
            "house", "pencil-square", "database", "bar-chart",
            "file-earmark-text", "calendar", "calendar-check", "calendar-week",
            "journal-check", "cash-coin", "building", "people",
            "diagram-3",
            "sliders",
            "person-circle", "funnel", "broadcast", "bell",
            "envelope-paper", "cloud-download", "file-pdf",
            "person-badge", "journal-text", "gear", "robot", "cloud-upload",
        ]
    elif user_role == "teacher":
        menu_options = [
            t("dashboard"), t("analyze"), t("database"), t("analytics"),
            t("reports"), t("attendance"), t("exams"), t("timetable"),
            t("assignments"), t("fees"), t("classes"), t("profile"),
            t("filters"), t("live"), t("notifications"), t("pdf_templates"),
            t("settings"), t("ml"), t("bulk_import"),
        ]
        menu_icons = [
            "house", "pencil-square", "database", "bar-chart",
            "file-earmark-text", "calendar", "calendar-check", "calendar-week",
            "journal-check", "cash-coin", "building", "person-circle",
            "funnel", "broadcast", "bell", "file-pdf",
            "gear", "robot", "cloud-upload",
        ]
    elif user_role == "parent":
        menu_options = [
            t("dashboard"), t("my_children"), t("attendance"),
            t("fees"), t("notifications"), t("live"), t("settings"),
        ]
        menu_icons = ["house", "people", "calendar", "cash-coin", "bell", "broadcast", "gear"]
    else:  # student
        menu_options = [
            t("dashboard"), t("my_results"), t("my_progress"),
            t("attendance"), t("assignments"), t("fees"),
            t("notifications"), t("live"), t("settings"),
        ]
        menu_icons = [
            "house", "bar-chart", "graph-up", "calendar",
            "journal-check", "cash-coin", "bell", "broadcast", "gear",
        ]

    selected = option_menu(
        menu_title=None, options=menu_options, icons=menu_icons,
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6366f1", "font-size": "0.95rem"},
            "nav-link": {"font-size": "0.83rem", "text-align": "left",
                         "margin": "0.1rem 0", "padding": "0.45rem 0.7rem",
                         "border-radius": "8px", "color": "inherit",
                         "--hover-color": "rgba(99,102,241,0.08)"},
            "nav-link-selected": {"background-color": "rgba(99,102,241,0.14)",
                                  "color": "#6366f1", "font-weight": "600",
                                  "border-left": "3px solid #6366f1"},
        }
    )

    st.markdown("---")
    st.caption(f"🔗 `{API_URL}`")
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code == 200:
            st.success("🟢 Online")
        else:
            st.error(f"🔴 Offline (HTTP {r.status_code})")
    except requests.exceptions.Timeout:
        st.warning("🟡 Backend waking up (cold start)")
    except Exception as _e:
        st.error(f"🔴 {type(_e).__name__}")

    st.markdown("---")
    if st.button(f"🔑 {t('change_password').replace('🔑 ', '')}", use_container_width=True):
        st.session_state.show_change_password = True
        st.rerun()
    if st.button(t("logout"), use_container_width=True):
        try:
            api_post("/auth/logout")
        except Exception:
            pass
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ============================================================
# PAGE: DASHBOARD
# ============================================================
if selected == t("dashboard"):
    st.markdown(f"""
        <div class="main-header">
            <h1>🏠 {t('welcome')}, {user_name}!</h1>
            <p>Your personalized dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    resp = api_get("/stats/overall")
    stats = handle_response(resp, show_error=False) if resp else None

    if stats and "total_students" in stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric("👥", stats["total_students"], "Total Students")
        with c2: render_metric("📈", f"{stats['average_of_averages']:.1f}", "Average Score")
        with c3: render_metric("✅", f"{stats['pass_rate']:.0f}%", "Pass Rate")
        with c4: render_metric("🏆", f"{stats['distinction_rate']:.0f}%", "Distinction")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if stats.get("grade_distribution"):
                st.markdown("### 📊 Grade Distribution")
                gdf = pd.DataFrame({"Grade": list(stats["grade_distribution"].keys()),
                                    "Count": list(stats["grade_distribution"].values())})
                st.plotly_chart(style_chart(px.pie(gdf, values="Count", names="Grade", hole=0.4)),
                              use_container_width=True)
        with c2:
            if stats.get("top_performers"):
                st.markdown("### 🏆 Top Performers")
                for i, s in enumerate(stats["top_performers"][:5], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
                    st.markdown(f"{medal} **{s['name']}** — {s['average']:.1f}% ({s['grade']})")


    # ============================================================
    # RECENT ACHIEVEMENTS (Feature 6)
    # ============================================================
    st.markdown("---")
    st.markdown("### 🏅 Recent Achievements")

    try:
        _recent_resp = api_get("/students", params={"limit": 500})
        _recent_data = handle_response(_recent_resp, show_error=False) if _recent_resp else None
        _recent_students = _recent_data.get("students", []) if _recent_data else []

        _all_recent = []
        for _s in _recent_students[:20]:
            _br = api_get(f"/students/{_s['id']}/badges")
            _bd = handle_response(_br, show_error=False) if _br else None
            for _b in (_bd.get("badges", []) if _bd else []):
                _b["student_name"] = _s["name"]
                _all_recent.append(_b)

        _all_recent.sort(key=lambda x: x.get("awarded_at", ""), reverse=True)
        _top5 = _all_recent[:5]

        if not _top5:
            st.info("No achievements awarded yet.")
        else:
            for _r in _top5:
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;gap:1rem;
                                background:rgba(99,102,241,0.08);
                                border-left:4px solid #6366f1;
                                padding:0.75rem 1rem;border-radius:8px;margin:0.4rem 0;">
                        <div style="font-size:1.8rem;">{_r.get('icon','🏅')}</div>
                        <div>
                            <b>{_r.get('name','')}</b>
                            <span style="color:#6b7280;font-size:0.85rem;">
                                — awarded to {_r.get('student_name','')}
                            </span>
                            <div style="font-size:0.75rem;color:#9ca3af;">
                                {_r.get('awarded_at','')[:16]}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except Exception as _e:
        st.caption(f"Could not load recent achievements: {_e}")

    else:
        st.info(f"👋 {t('welcome')}! Get started by adding students.")


# ============================================================
# PAGE: ANALYZE
# ============================================================
elif selected == t("analyze"):
    st.markdown(f'<div class="main-header"><h1>{t("analyze")}</h1><p>Enter marks and get insights</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        student_name = st.text_input("👤 Student Name *", placeholder="John Doe", key="an_name")
        c1, c2, c3, c4 = st.columns(4)
        with c1: semester = st.selectbox("Semester", ["Fall 2024", "Spring 2024", "Summer 2024"], key="an_sem")
        with c2: batch_year = st.selectbox("Batch Year", ["2024", "2023", "2022", "2021"], key="an_year")
        with c3: department = st.selectbox("Department", ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"], key="an_dept")
        with c4: class_name = st.text_input("Class (optional)", placeholder="CS-A", key="an_class")

        num_subjects = st.slider("Number of Subjects", 1, 15, 5, key="an_num")
        marks, subject_names = [], []
        cols = st.columns(3)
        for i in range(num_subjects):
            with cols[i % 3]:
                subj = st.text_input(f"Subject {i+1}", key=f"an_subj_{i}", label_visibility="collapsed")
                mark = st.number_input(f"Marks {i+1}", 0, 100, 0, 1, key=f"an_mark_{i}", label_visibility="collapsed")
                marks.append(mark)
                subject_names.append(subj or f"Subject {i+1}")

    with col2:
        st.markdown("### ⚙️ Settings")
        passing = st.slider("Passing Threshold", 0, 60, 40, 5, key="an_pass")
        scheme = st.selectbox("Grade Scheme", ["standard", "strict", "lenient"], key="an_scheme")
        if sum(marks) > 0:
            st.metric("Average", f"{sum(marks)/len(marks):.1f}%")

    if st.button("🚀 Analyze Performance", type="primary", use_container_width=True):
        if sum(marks) == 0 or not student_name:
            st.warning("Fill name and marks")
        else:
            payload = {"marks": marks, "student_name": student_name, "subject_names": subject_names,
                       "passing_threshold": passing, "grade_scheme": scheme,
                       "semester": semester, "batch_year": batch_year, "department": department,
                       "class_name": class_name or None}
            resp = api_post("/analyze", json=payload)
            data = handle_response(resp) if resp else None
            if data:
                st.session_state.analyze_result = data
                st.success("Analysis complete!")
                st.balloons()

    if st.session_state.analyze_result:
        res = st.session_state.analyze_result
        st.markdown("---")
        gc = {"A+": "#10b981", "A": "#34d399", "B": "#fbbf24", "C": "#f59e0b", "D": "#f97316", "E": "#ef4444", "F": "#dc2626"}.get(res["grade"], "#6366f1")
        st.markdown(f"""
            <div style="text-align: center; padding: 1rem 0;">
                <h2>Overall Grade</h2>
                <div style="font-size: 2.5rem; font-weight: 800; padding: 1.2rem 2.5rem;
                            border-radius: 100px; display: inline-block;
                            background: {gc}; color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
                    {res['grade']} <span style="font-size: 1.3rem;">(GPA: {res['grade_points']})</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric("📊", f"{res['average']:.1f}%", "Average")
        with c2: render_metric("📈", f"{res['total_marks']:.0f}", "Total")
        with c3: render_metric("🏆", f"{res['highest']:.0f}", "Highest")
        with c4: render_metric("✅", f"{res['pass_percentage']:.0f}%", "Pass Rate")

        df = pd.DataFrame(res["subject_wise"])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["subject"], y=df["marks"],
                             marker_color=["#10b981" if m >= passing else "#ef4444" for m in df["marks"]],
                             text=df["marks"], textposition="outside"))
        fig.update_layout(yaxis_range=[0, 105], showlegend=False)
        st.plotly_chart(style_chart(fig), use_container_width=True)

        st.markdown("### 💡 Recommendations")
        for rec in res["recommendations"]:
            st.markdown(f'<div class="recommendation-card">{rec}</div>', unsafe_allow_html=True)

        if st.button("💾 Save Student Record", type="primary", use_container_width=True):
            save_data = {"name": res["student_name"], "marks": marks, "subjects": subject_names,
                         "grade": res["grade"], "average": res["average"],
                         "total_marks": res["total_marks"], "timestamp": datetime.now().isoformat(),
                         "semester": semester, "batch_year": batch_year, "department": department,
                         "class_name": class_name or None}
            r = api_post("/students/save", json=save_data)
            if r and r.status_code == 200:
                st.success("Saved!")
                st.balloons()


# ============================================================
# PAGE: DATABASE
# ============================================================
elif selected == t("database"):
    st.markdown(f'<div class="main-header"><h1>{t("database")}</h1><p>Manage students</p></div>', unsafe_allow_html=True)

    resp = api_get("/students", params={"limit": 500})
    data = handle_response(resp, show_error=False) if resp else None

    if data and data["count"] > 0:
        st.success(f"Total: {data['count']} students")

        df = pd.DataFrame(data["students"])
        df["select"] = False
        display_cols = ["select", "id", "name", "grade", "average", "class_name", "department"]
        available = [c for c in display_cols if c in df.columns]

        edited = st.data_editor(
            df[available],
            use_container_width=True,
            hide_index=True,
            column_config={
                "select": st.column_config.CheckboxColumn("✓", default=False),
            },
            key="db_editor",
        )

        selected_ids = edited[edited["select"] == True]["id"].tolist()

        if selected_ids:
            st.info(f"**{len(selected_ids)} selected**")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"🗑️ Delete {len(selected_ids)} students", type="secondary", use_container_width=True):
                    r = api_post("/students/bulk-delete", json={"student_ids": selected_ids})
                    if r and r.status_code == 200:
                        st.success(r.json()["message"])
                        time.sleep(0.5)
                        st.rerun()
            with c2:
                if st.button(f"📢 Send notification to {len(selected_ids)}", use_container_width=True):
                    st.session_state.show_bulk_notif = True

            if st.session_state.get("show_bulk_notif"):
                with st.form("bulk_notif_form"):
                    msg = st.text_input("Notification message")
                    ntype = st.selectbox("Type", ["Info", "Warning", "Achievement"])
                    if st.form_submit_button("Send"):
                        r = api_post("/notifications/bulk-send",
                                     json={"student_ids": selected_ids,
                                           "message": msg, "type": ntype})
                        if r and r.status_code == 200:
                            st.success(r.json()["message"])
                            st.session_state.show_bulk_notif = False

        st.markdown("### 📄 Generate Report Card")
        opts = {f"{s['name']} (ID: {s['id']})": s["id"] for s in data["students"]}
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1: sel = st.selectbox("Student", list(opts.keys()), key="pdf_sel")
        with c2:
            pdf_template = st.selectbox("Template", ["classic", "modern", "minimal"], key="pdf_tpl")
        with c3:
            if st.button("📄 Generate", use_container_width=True):
                sid = opts[sel]
                endpoint = (f"/students/{sid}/report-card"
                            if pdf_template == "classic"
                            else f"/students/{sid}/report-card/{pdf_template}")
                r = api_get(endpoint)
                if r and r.status_code == 200:
                    st.download_button("💾 Download", data=r.content,
                                      file_name=f"report_{sid}_{pdf_template}.pdf",
                                      mime="application/pdf")
    else:
        st.info("No students yet")


# ============================================================
# PAGE: BULK IMPORT (NEW)
# ============================================================
elif selected == t("bulk_import"):
    st.markdown(f'<div class="main-header"><h1>{t("bulk_import")}</h1><p>Import multiple students from CSV with preview</p></div>', unsafe_allow_html=True)

    st.markdown("### 📥 Step 1 — Upload or paste CSV")
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("📋 Download Template", use_container_width=True):
            r = api_get("/students/import-template")
            if r and r.status_code == 200:
                st.download_button("💾 Save Template", data=r.content,
                                   file_name="students_template.csv", mime="text/csv")

    uploaded = st.file_uploader("Upload CSV file", type=["csv"])
    csv_text = None
    if uploaded:
        try:
            csv_text = uploaded.read().decode("utf-8")
            st.success(f"✅ File loaded: {uploaded.name}")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    st.markdown("Or paste CSV text manually:")
    pasted = st.text_area("CSV Text", height=150,
                          placeholder="name,marks,subjects,semester,department,class_name\nJohn Doe,\"85,92,78\",\"Math,Science,English\",Fall 2024,CS,CS-A")
    if pasted and not csv_text:
        csv_text = pasted

    if csv_text:
        st.markdown("---")
        st.markdown("### 🔍 Step 2 — Preview & Validate")

        if st.button("🔍 Preview Import", type="primary", use_container_width=True):
            r = api_post("/students/bulk-import/preview", json={"csv_text": csv_text})
            result = handle_response(r, show_error=False) if r else None
            if result:
                st.session_state.bulk_import_preview = result
            else:
                st.error("Preview failed. Check backend.")

        preview = st.session_state.get("bulk_import_preview")
        if preview:
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("✅ Valid Rows", preview["valid_rows"])
            with c2: st.metric("❌ Errors", preview["error_count"])
            with c3: st.metric("📊 Total", preview["total"])

            if preview["error_count"] > 0:
                st.warning("⚠️ Some rows have errors — fix them before importing.")
                with st.expander(f"Show {preview['error_count']} error(s)", expanded=True):
                    err_df = pd.DataFrame(preview["errors"])
                    st.dataframe(err_df, use_container_width=True)

            if preview["valid_rows"] > 0:
                st.markdown("### 📋 Valid Rows Preview")
                valid_df = pd.DataFrame(preview["preview"])
                st.dataframe(valid_df, use_container_width=True)

                st.markdown("---")
                st.markdown("### ✅ Step 3 — Commit Import")
                if st.button(f"🚀 Import {preview['valid_rows']} Students",
                            type="primary", use_container_width=True):
                    commit_body = {"rows": preview["preview"]}
                    r = api_post("/students/bulk-import/commit", json=commit_body)
                    result = handle_response(r) if r else None
                    if result:
                        st.success(f"✅ Imported {result['imported']} students!")
                        if result.get("failed_count", 0) > 0:
                            st.warning(f"{result['failed_count']} rows failed")
                            st.json(result.get("failed", []))
                        st.balloons()
                        st.session_state.bulk_import_preview = None
                        time.sleep(2)
                        st.rerun()


# ============================================================
# PAGE: ANALYTICS
# ============================================================
elif selected == t("analytics"):
    st.markdown(f'<div class="main-header"><h1>{t("analytics")}</h1></div>', unsafe_allow_html=True)

    resp = api_get("/analytics/dashboard")
    data = handle_response(resp, show_error=False) if resp else None

    if data and data.get("has_data"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_metric("👥", data["total_students"], "Students")
        with c2: render_metric("📈", f"{data['overall_average']:.1f}", "Average")
        with c3: render_metric("✅", f"{data['pass_rate']:.1f}%", "Pass Rate")
        with c4: render_metric("🏆", f"{data['distinction_rate']:.1f}%", "Distinction")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if data.get("grade_distribution"):
                gdf = pd.DataFrame({"Grade": list(data["grade_distribution"].keys()),
                                    "Count": list(data["grade_distribution"].values())})
                st.plotly_chart(style_chart(px.pie(gdf, values="Count", names="Grade", hole=0.4)),
                              use_container_width=True)
        with c2:
            if data.get("grade_ranges"):
                rdf = pd.DataFrame({"Range": list(data["grade_ranges"].keys()),
                                    "Count": list(data["grade_ranges"].values())})
                st.plotly_chart(style_chart(px.bar(rdf, x="Range", y="Count", color="Count",
                                       color_continuous_scale="Viridis")), use_container_width=True)
        if data.get("subject_analytics"):
            subj_df = pd.DataFrame(data["subject_analytics"])
            st.plotly_chart(style_chart(px.bar(subj_df, x="subject", y="average", color="average",
                                   color_continuous_scale="RdYlGn")), use_container_width=True)

        # ============================================================
        # SUBJECT × STUDENT HEATMAP
        # ============================================================
        st.markdown("---")
        st.markdown("### 🔥 Subject-wise Heatmap")
        st.caption("Every student's marks across every subject. Red = struggling, green = strong.")

        # Fetch all students
        _hm_resp = api_get("/students", params={"limit": 500})
        _hm_data = handle_response(_hm_resp, show_error=False) if _hm_resp else None
        _hm_students = _hm_data.get("students", []) if _hm_data else []

        if not _hm_students:
            st.info("No students available for heatmap.")
        else:
            # Optional class filter
            _hm_classes = sorted(set(
                s.get("class_name") for s in _hm_students if s.get("class_name")
            ))
            _hm_filter_col1, _hm_filter_col2 = st.columns([2, 2])
            with _hm_filter_col1:
                _hm_class = st.selectbox(
                    "Filter by class",
                    options=["All"] + _hm_classes,
                    key="hm_class_filter",
                )
            with _hm_filter_col2:
                _hm_sort = st.selectbox(
                    "Sort students by",
                    options=["Name", "Average (high → low)", "Average (low → high)"],
                    key="hm_sort_mode",
                )

            _hm_filtered = _hm_students if _hm_class == "All" else [
                s for s in _hm_students if s.get("class_name") == _hm_class
            ]

            # Build the matrix
            _hm_subjects = []
            for s in _hm_filtered:
                for subj in s.get("subjects", []):
                    if subj and subj not in _hm_subjects:
                        _hm_subjects.append(subj)

            # Sort students
            if _hm_sort == "Average (high → low)":
                _hm_filtered = sorted(_hm_filtered, key=lambda s: s.get("average", 0), reverse=True)
            elif _hm_sort == "Average (low → high)":
                _hm_filtered = sorted(_hm_filtered, key=lambda s: s.get("average", 0))
            else:
                _hm_filtered = sorted(_hm_filtered, key=lambda s: s.get("name", ""))

            # Build 2D array: rows = students, cols = subjects
            import plotly.graph_objects as _go

            _hm_names = [s["name"] for s in _hm_filtered]
            _hm_matrix = []
            _hm_text = []  # hover text
            for s in _hm_filtered:
                subj_map = dict(zip(s.get("subjects", []), s.get("marks", [])))
                row = []
                txt_row = []
                for subj in _hm_subjects:
                    val = subj_map.get(subj)
                    row.append(val if val is not None else None)
                    txt_row.append(f"{val:.0f}" if val is not None else "—")
                _hm_matrix.append(row)
                _hm_text.append(txt_row)

            if not _hm_subjects:
                st.info("No subject data available.")
            else:
                _hm_colors = get_chart_colors()

                _hm_fig = _go.Figure(data=_go.Heatmap(
                    z=_hm_matrix,
                    x=_hm_subjects,
                    y=_hm_names,
                    text=_hm_text,
                    texttemplate="%{text}",
                    textfont={"size": 11},
                    colorscale=[
                        [0.0, "#ef4444"],   # 0   → red
                        [0.4, "#f59e0b"],   # 40  → amber
                        [0.6, "#fbbf24"],   # 60  → yellow
                        [0.8, "#84cc16"],   # 80  → lime
                        [1.0, "#10b981"],   # 100 → green
                    ],
                    zmin=0,
                    zmax=100,
                    hovertemplate="<b>%{y}</b><br>%{x}: %{z:.0f}<extra></extra>",
                    colorbar=dict(
                        title=dict(text="Mark", font=dict(color=_hm_colors["text"])),
                        tickfont=dict(color=_hm_colors["text"]),
                    ),
                ))
                _hm_fig.update_layout(
                    height=max(300, 40 + 28 * len(_hm_filtered)),
                    xaxis=dict(side="top", tickfont=dict(color=_hm_colors["text"])),
                    yaxis=dict(autorange="reversed", tickfont=dict(color=_hm_colors["text"])),
                    margin=dict(l=20, r=20, t=60, b=20),
                )
                st.plotly_chart(style_chart(_hm_fig), use_container_width=True)

                # Quick legend
                _hm_legend_col1, _hm_legend_col2, _hm_legend_col3 = st.columns(3)
                with _hm_legend_col1:
                    st.markdown(
                        '<span style="color:#ef4444;font-weight:600;">● 0-39</span> Needs urgent help',
                        unsafe_allow_html=True,
                    )
                with _hm_legend_col2:
                    st.markdown(
                        '<span style="color:#fbbf24;font-weight:600;">● 40-79</span> Average',
                        unsafe_allow_html=True,
                    )
                with _hm_legend_col3:
                    st.markdown(
                        '<span style="color:#10b981;font-weight:600;">● 80-100</span> Excellent',
                        unsafe_allow_html=True,
                    )

        if data.get("top_performers"):
            st.markdown("### 🏆 Top Performers")
            st.dataframe(pd.DataFrame(data["top_performers"]), use_container_width=True)
    else:
        st.info("No data yet")


# ============================================================
# PAGE: REPORTS (Export)
# ============================================================
elif selected == t("reports"):
    st.markdown(f'<div class="main-header"><h1>{t("reports")}</h1><p>Export data</p></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 Export CSV", use_container_width=True):
            r = api_get("/export/csv")
            if r and r.status_code == 200:
                st.download_button("💾 Download CSV", data=r.content,
                                  file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                                  mime="text/csv")
    with c2:
        if st.button("📋 Export JSON", use_container_width=True):
            r = api_get("/export/json")
            if r and r.status_code == 200:
                st.download_button("💾 Download JSON", data=json.dumps(r.json(), indent=2),
                                  file_name=f"students_{datetime.now().strftime('%Y%m%d')}.json",
                                  mime="application/json")
    with c3:
        if st.button("📈 Export Excel", use_container_width=True):
            r = api_get("/export/excel")
            if r and r.status_code == 200:
                st.download_button("💾 Download .xlsx", data=r.content,
                                  file_name=f"students_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================
    # EXAM RESULTS BULK IMPORT (Feature 14)
    # ============================================================
    st.markdown("---")
    st.markdown("### Exam Results Bulk Import")
    st.caption("Upload CSV of exam marks. Grades auto-computed on commit.")

    if user_role not in ("admin", "teacher"):
        st.info("Only admins and teachers can import exam results.")
    else:
        with st.expander("Import Exam Results from CSV", expanded=False):
            _tpl_c1, _tpl_c2 = st.columns([3, 1])
            with _tpl_c2:
                if st.button("Template", use_container_width=True, key="exam_tpl_btn"):
                    _tr = api_get("/exam-results/template")
                    if _tr and _tr.status_code == 200:
                        st.download_button("Save Template", data=_tr.content,
                                          file_name="exam_results_template.csv",
                                          mime="text/csv", key="exam_tpl_save")

            _up = st.file_uploader("Upload CSV", type=["csv"], key="exam_csv_upload")
            _csv_text = None
            if _up:
                try:
                    _csv_text = _up.read().decode("utf-8")
                    st.success("Loaded: " + _up.name)
                except Exception as _e:
                    st.error("Read failed: " + str(_e))

            _pasted = st.text_area(
                "Or paste CSV:",
                height=120,
                placeholder="student_name,subject,exam_name,marks,total_marks",
                key="exam_csv_paste",
            )
            if _pasted and not _csv_text:
                _csv_text = _pasted

            if _csv_text:
                if st.button("Preview", type="primary", key="exam_prev_btn"):
                    _pr = api_post("/exam-results/preview", json={"csv_text": _csv_text})
                    _prd = handle_response(_pr, show_error=False) if _pr else None
                    if _prd:
                        st.session_state["exam_import_preview"] = _prd

                _preview = st.session_state.get("exam_import_preview")
                if _preview:
                    _m1, _m2, _m3 = st.columns(3)
                    with _m1: st.metric("Valid", _preview.get("valid_rows", 0))
                    with _m2: st.metric("Errors", _preview.get("error_count", 0))
                    with _m3: st.metric("Total", _preview.get("total", 0))

                    if _preview.get("error_count", 0) > 0:
                        with st.expander("Show errors"):
                            import pandas as _pd
                            st.dataframe(_pd.DataFrame(_preview.get("errors", [])), use_container_width=True)

                    if _preview.get("valid_rows", 0) > 0:
                        import pandas as _pd2
                        st.dataframe(_pd2.DataFrame(_preview.get("preview", [])),
                                    use_container_width=True, hide_index=True)

                        if st.button("Import " + str(_preview.get("valid_rows", 0)) + " rows",
                                    type="primary", key="exam_commit_btn"):
                            _cr = api_post("/exam-results/commit",
                                          json={"rows": _preview.get("preview", [])})
                            _crd = handle_response(_cr, show_error=False) if _cr else None
                            if _crd:
                                st.success("Imported " + str(_crd.get("imported", 0)) + " rows!")
                                st.balloons()
                                st.session_state.pop("exam_import_preview", None)
                                time.sleep(1.5)
                                st.rerun()


# ============================================================
# PAGE: ATTENDANCE
# ============================================================
elif selected == t("attendance") or selected == "📅 My Attendance":
    st.markdown(f'<div class="main-header"><h1>{t("attendance")}</h1></div>', unsafe_allow_html=True)

    if user_role in ["admin", "teacher"]:
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Single", "📋 Bulk", "📊 Overall", "📈 Trends"])

        with tab1:
            r = api_get("/students", params={"limit": 500})
            data = handle_response(r, show_error=False) if r else None
            students = data.get("students", []) if data else []
            if students:
                c1, c2 = st.columns(2)
                with c1: d = st.date_input("Date", datetime.now())
                with c2: s = st.text_input("Subject (optional)")
                opts = {f"{x['name']}": x["id"] for x in students}
                sel = st.selectbox("Student", list(opts.keys()))
                status = st.selectbox("Status", ["Present", "Absent", "Late", "Excused"])
                if st.button("📝 Record", type="primary", use_container_width=True):
                    r = api_post("/attendance", json={"student_id": opts[sel],
                                                      "date": d.isoformat(),
                                                      "status": status, "subject": s or None})
                    if r and r.status_code == 200:
                        st.success("Recorded!")

        with tab2:
            r = api_get("/students", params={"limit": 500})
            data = handle_response(r, show_error=False) if r else None
            students = data.get("students", []) if data else []
            if students:
                c1, c2 = st.columns(2)
                with c1: bd = st.date_input("Date", datetime.now(), key="bulk_d")
                with c2: bs = st.text_input("Subject", key="bulk_s")
                classes = list(set(s.get("class_name") for s in students if s.get("class_name")))
                class_filter = st.selectbox("Filter by class", ["All"] + classes)
                filtered = students if class_filter == "All" else [s for s in students if s.get("class_name") == class_filter]
                st.caption(f"{len(filtered)} students")
                selected_bulk = st.multiselect("Select students", [f"{s['name']} (ID {s['id']})" for s in filtered])
                bstatus = st.selectbox("Status", ["Present", "Absent", "Late", "Excused"], key="bulk_status")
                if st.button("📋 Record Bulk", type="primary", use_container_width=True):
                    if selected_bulk:
                        ids = [int(x.split("ID ")[1].rstrip(")")) for x in selected_bulk]
                        r = api_post("/attendance/bulk", json={
                            "student_ids": ids, "date": bd.isoformat(),
                            "status": bstatus, "subject": bs or None,
                        })
                        if r and r.status_code == 200:
                            st.success(r.json()["message"])
                            st.balloons()

        with tab3:
            r = api_get("/attendance/stats/overall")
            data = handle_response(r, show_error=False) if r else None
            if data and data.get("total_records", 0) > 0:
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Records", data["total_records"])
                with c2: st.metric("Present", data["present"])
                with c3: st.metric("Absent", data["absent"])
                with c4: st.metric("Rate", f"{data['overall_rate']:.1f}%")

        with tab4:
            st.markdown("### 📈 Attendance Trends")
            st.caption("Daily attendance rate over time")

            days_choice = st.selectbox(
                "Time range",
                options=[7, 30, 90, 180],
                index=1,
                format_func=lambda x: f"Last {x} days",
                key="att_trend_days",
            )

            try:
                trend_resp = api_get(f"/attendance/trends?days={days_choice}")
                trend_data = handle_response(trend_resp, show_error=False) if trend_resp else None
            except Exception as _e:
                trend_data = None
                st.error(f"Failed to load trends: {_e}")

            if not trend_data or not trend_data.get("trends"):
                st.info(
                    "No attendance records found in this time range. "
                    "Add attendance via the **📝 Single** or **📋 Bulk** tabs."
                )
            else:
                trends = trend_data["trends"]
                summary = trend_data.get("summary", {})

                m1, m2, m3 = st.columns(3)
                with m1:
                    avg = summary.get("avg_rate", 0)
                    color = "#10b981" if avg >= 80 else "#f59e0b" if avg >= 60 else "#ef4444"
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-icon">📊</div>
                            <div class="metric-value" style="color:{color};">{avg:.1f}%</div>
                            <div class="metric-label">Average Rate</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with m2:
                    best = summary.get("best_day") or {}
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-icon">🏆</div>
                            <div class="metric-value" style="color:#10b981;">{best.get('rate', 0):.1f}%</div>
                            <div class="metric-label">Best Day</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with m3:
                    worst = summary.get("worst_day") or {}
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-icon">⚠️</div>
                            <div class="metric-value" style="color:#ef4444;">{worst.get('rate', 0):.1f}%</div>
                            <div class="metric-label">Worst Day</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("---")

                import plotly.graph_objects as _go
                import pandas as _pd

                tdf = _pd.DataFrame(trends)
                tdf["date"] = _pd.to_datetime(tdf["date"])
                colors = get_chart_colors()

                fig = _go.Figure()
                fig.add_trace(_go.Scatter(
                    x=tdf["date"], y=tdf["rate"], mode="lines+markers",
                    name="Attendance Rate",
                    line=dict(color=colors["primary"], width=3),
                    marker=dict(size=8, color=colors["primary"]),
                    fill="tozeroy",
                    fillcolor="rgba(99,102,241,0.15)",
                ))
                fig.add_hline(y=80, line=dict(color=colors["success"], width=1, dash="dash"),
                              annotation_text="Target (80%)", annotation_position="top left")
                fig.update_yaxes(range=[0, 105], title="Attendance Rate (%)")
                fig.update_xaxes(title="Date")
                fig.update_layout(height=400, showlegend=False,
                                  title=f"Attendance Rate (Last {days_choice} Days)")
                st.plotly_chart(style_chart(fig), use_container_width=True)

                with st.expander("📋 View daily data"):
                    disp = tdf.copy()
                    disp["date"] = disp["date"].dt.strftime("%Y-%m-%d")
                    disp["rate"] = disp["rate"].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(disp[["date", "present", "absent", "late", "excused", "total", "rate"]],
                                 use_container_width=True, hide_index=True)
    else:
        st.info("Your attendance summary")

# ============================================================
# PAGE: EXAMS
# ============================================================
elif selected == t("exams"):
    st.markdown(f'<div class="main-header"><h1>{t("exams")}</h1><p>Manage exam schedules</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 All Exams", "➕ Create"])

    with tab1:
        r = api_get("/exams")
        data = handle_response(r, show_error=False) if r else None
        exams = data.get("exams", []) if data else []

        if exams:
            st.metric("Total Exams", len(exams))
            df = pd.DataFrame(exams)
            if not df.empty:
                display_cols = ["id", "name", "class_name", "subject", "exam_date", "start_time", "total_marks"]
                available = [c for c in display_cols if c in df.columns]
                st.dataframe(df[available], use_container_width=True)

            if user_role in ["admin", "teacher"]:
                st.markdown("### 🗑️ Delete Exam")
                exam_opts = {f"{e['name']} ({e['exam_date']})": e["id"] for e in exams}
                if exam_opts:
                    sel_exam = st.selectbox("Select exam to delete", list(exam_opts.keys()))
                    if st.button("🗑️ Delete", type="secondary"):
                        r = api_delete(f"/exams/{exam_opts[sel_exam]}")
                        if r and r.status_code == 200:
                            st.success("Deleted!")
                            time.sleep(0.5)
                            st.rerun()
        else:
            st.info("No exams yet. Create one in the next tab.")

    with tab2:
        if user_role in ["admin", "teacher"]:
            st.markdown("### Create Exam")
            with st.form("create_exam"):
                en = st.text_input("Exam Name *", placeholder="Mid-Term 2024")
                c1, c2 = st.columns(2)
                with c1:
                    ec = st.text_input("Class", placeholder="CS-A")
                    es = st.text_input("Subject", placeholder="Mathematics")
                with c2:
                    ed = st.date_input("Exam Date")
                    er = st.text_input("Room", placeholder="Room 101")

                c1, c2, c3 = st.columns(3)
                with c1: est = st.text_input("Start Time", placeholder="09:00")
                with c2: eet = st.text_input("End Time", placeholder="11:00")
                with c3: etm = st.number_input("Total Marks", 0, 500, 100)

                enotes = st.text_area("Notes")

                if st.form_submit_button("➕ Create Exam", type="primary"):
                    if not en:
                        st.warning("Enter exam name")
                    else:
                        payload = {
                            "name": en, "class_name": ec or None,
                            "subject": es or None, "exam_date": ed.isoformat(),
                            "start_time": est or None, "end_time": eet or None,
                            "total_marks": etm, "room": er or None, "notes": enotes or None,
                        }
                        r = api_post("/exams/create", json=payload)
                        if r and r.status_code == 200:
                            st.success("Exam created!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Failed"))
        else:
            st.info("Only admins and teachers can create exams")


# ============================================================
# PAGE: TIMETABLE
# ============================================================
elif selected == t("timetable"):
    st.markdown(f'<div class="main-header"><h1>{t("timetable")}</h1><p>Weekly class schedule</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 View", "➕ Add Entry"])

    with tab1:
        r = api_get("/timetable")
        data = handle_response(r, show_error=False) if r else None
        entries = data.get("timetable", []) if data else []

        if entries:
            classes = list(set(e["class_name"] for e in entries))
            selected_class = st.selectbox("Select class", classes)
            filtered = [e for e in entries if e["class_name"] == selected_class]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            df = pd.DataFrame(filtered)
            st.markdown(f"### 📅 Timetable for {selected_class}")
            if not df.empty:
                df_pivot = df.pivot_table(index="day_of_week", columns="period",
                                          values="subject", aggfunc="first")
                df_pivot = df_pivot.reindex(days)
                st.dataframe(df_pivot, use_container_width=True)
        else:
            st.info("No timetable entries yet")

    with tab2:
        if user_role in ["admin", "teacher"]:
            st.markdown("### Add Timetable Entry")
            with st.form("create_tt"):
                c1, c2 = st.columns(2)
                with c1:
                    tcn = st.text_input("Class Name *", placeholder="CS-A")
                    tdow = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
                    tsub = st.text_input("Subject *", placeholder="Mathematics")
                with c2:
                    tper = st.number_input("Period", 1, 10, 1)
                    tteacher = st.text_input("Teacher Name", placeholder="Mr. Smith")
                    troom = st.text_input("Room", placeholder="Room 101")

                c1, c2 = st.columns(2)
                with c1: tstart = st.text_input("Start Time", placeholder="09:00")
                with c2: tend = st.text_input("End Time", placeholder="10:00")

                if st.form_submit_button("➕ Add Entry", type="primary"):
                    if not tcn or not tsub:
                        st.warning("Enter class and subject")
                    else:
                        payload = {
                            "class_name": tcn, "day_of_week": tdow, "period": tper,
                            "subject": tsub, "teacher_name": tteacher or None,
                            "room": troom or None, "start_time": tstart or None,
                            "end_time": tend or None,
                        }
                        r = api_post("/timetable/create", json=payload)
                        if r and r.status_code == 200:
                            st.success("Added!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Failed"))
        else:
            st.info("Only admins and teachers can add timetable entries")


# ============================================================
# PAGE: ASSIGNMENTS
# ============================================================
elif selected == t("assignments"):
    st.markdown(f'<div class="main-header"><h1>{t("assignments")}</h1><p>Track assignments and submissions</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 All", "➕ Create"])

    with tab1:
        r = api_get("/assignments")
        data = handle_response(r, show_error=False) if r else None
        assignments = data.get("assignments", []) if data else []

        if assignments:
            st.metric("Total Assignments", len(assignments))
            for a in assignments:
                with st.expander(f"📝 {a['title']} — Due: {a['due_date'][:10]}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Class:** {a.get('class_name', 'N/A')}")
                        st.markdown(f"**Subject:** {a.get('subject', 'N/A')}")
                    with c2:
                        st.markdown(f"**Total Marks:** {a.get('total_marks', 100)}")
                        st.markdown(f"**Due Date:** {a.get('due_date', 'N/A')}")
                    with c3:
                        stats = a.get("stats", {})
                        st.markdown(f"**Submitted:** {stats.get('submitted', 0)}/{stats.get('total', 0)}")
                        st.markdown(f"**Graded:** {stats.get('graded', 0)}")

                    if a.get("description"):
                        st.markdown(f"**Description:** {a['description']}")

                    if user_role in ["admin", "teacher"]:
                        if st.button(f"👥 View Submissions", key=f"sub_{a['id']}"):
                            r = api_get(f"/assignments/{a['id']}/submissions")
                            subs = handle_response(r, show_error=False) if r else None
                            if subs and subs.get("submissions"):
                                sub_df = pd.DataFrame(subs["submissions"])
                                st.dataframe(sub_df, use_container_width=True)
        else:
            st.info("No assignments yet")

    with tab2:
        if user_role in ["admin", "teacher"]:
            st.markdown("### Create Assignment")
            with st.form("create_assignment"):
                at = st.text_input("Title *", placeholder="Chapter 5 Homework")
                ad = st.text_area("Description")
                c1, c2 = st.columns(2)
                with c1:
                    ac = st.text_input("Class", placeholder="CS-A")
                    asub = st.text_input("Subject", placeholder="Mathematics")
                with c2:
                    adue = st.date_input("Due Date")
                    atm = st.number_input("Total Marks", 0, 500, 100)

                if st.form_submit_button("➕ Create", type="primary"):
                    if not at:
                        st.warning("Enter title")
                    else:
                        payload = {
                            "title": at, "description": ad or None,
                            "class_name": ac or None, "subject": asub or None,
                            "due_date": adue.isoformat(), "total_marks": atm,
                        }
                        r = api_post("/assignments/create", json=payload)
                        if r and r.status_code == 200:
                            st.success("Created!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Failed"))


# ============================================================
# PAGE: FEES
# ============================================================
elif selected == t("fees"):
    st.markdown(f'<div class="main-header"><h1>{t("fees")}</h1><p>Fee structure and payments</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["💵 Payments", "📋 Structure", "➕ Record Payment", "⏰ Reminders"])

    with tab1:
        r = api_get("/fees/payments")
        data = handle_response(r, show_error=False) if r else None
        if data and data.get("payments"):
            summary = data.get("summary", {})
            c1, c2, c3 = st.columns(3)
            with c1: render_metric("💰", f"₹{summary.get('total_paid', 0):.0f}", "Total Paid")
            with c2: render_metric("⏳", f"₹{summary.get('total_pending', 0):.0f}", "Pending")
            with c3: render_metric("📊", summary.get("count", 0), "Total Records")
            st.markdown("---")
            df = pd.DataFrame(data["payments"])
            display_cols = ["id", "student_name", "fee_type", "amount", "payment_date", "payment_method", "status"]
            available = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True)

            # ---------- INVOICE GENERATION (Feature 8) ----------
            st.markdown("---")
            st.markdown("#### 🧾 Generate Invoices")
            st.caption("Download individual invoices or bulk-generate a ZIP.")

            _inv_c1, _inv_c2 = st.columns([2, 2])

            with _inv_c1:
                _inv_pay_opts = {
                    f"#{p['id']} — {p.get('student_name','?')} — ₹{p.get('amount',0):.0f}": p["id"]
                    for p in data["payments"][:50]
                }
                _inv_sel = st.selectbox(
                    "Select a payment",
                    options=list(_inv_pay_opts.keys()),
                    key="invoice_single_select",
                )
                if st.button("🖨️ Download Invoice", type="primary", use_container_width=True, key="inv_single_btn"):
                    _pid = _inv_pay_opts[_inv_sel]
                    _ir = api_get(f"/fees/payment/{_pid}/invoice")
                    if _ir and _ir.status_code == 200:
                        st.download_button(
                            "💾 Save PDF",
                            data=_ir.content,
                            file_name=f"invoice_{_pid}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"inv_dl_{_pid}",
                        )
                    else:
                        st.error("Failed to generate invoice")

            with _inv_c2:
                _inv_bulk_opts = {
                    f"#{p['id']} — {p.get('student_name','?')} — ₹{p.get('amount',0):.0f}": p["id"]
                    for p in data["payments"][:50]
                }
                _inv_bulk_sel = st.multiselect(
                    "Select payments for bulk download",
                    options=list(_inv_bulk_opts.keys()),
                    key="invoice_bulk_select",
                )
                if st.button("📦 Download ZIP", use_container_width=True, key="inv_bulk_btn",
                             disabled=not _inv_bulk_sel):
                    _pids = [_inv_bulk_opts[k] for k in _inv_bulk_sel]
                    _ir = api_post("/fees/invoices/bulk", json={"payment_ids": _pids})
                    if _ir and _ir.status_code == 200:
                        st.download_button(
                            "💾 Save ZIP",
                            data=_ir.content,
                            file_name=f"invoices_{len(_pids)}.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key="inv_bulk_dl",
                        )
                    else:
                        st.error("Failed to generate ZIP")


        else:
            st.info("No payments recorded yet")

    with tab2:
        r = api_get("/fees/structure")
        data = handle_response(r, show_error=False) if r else None
        structures = data.get("structures", []) if data else []
        if structures:
            st.metric("Fee Structures", len(structures))
            st.dataframe(pd.DataFrame(structures), use_container_width=True)
            if user_role == "admin":
                st.markdown("### 🗑️ Delete Structure")
                opts = {f"{s['class_name']} - {s['fee_type']} (₹{s['amount']})": s["id"] for s in structures}
                sel = st.selectbox("Select", list(opts.keys()))
                if st.button("🗑️ Delete", type="secondary"):
                    r = api_delete(f"/fees/structure/{opts[sel]}")
                    if r and r.status_code == 200:
                        st.success("Deleted!")
                        st.rerun()
        else:
            st.info("No fee structures yet")

        if user_role == "admin":
            st.markdown("### ➕ Create Fee Structure")
            with st.form("create_fee_structure"):
                c1, c2 = st.columns(2)
                with c1:
                    fsc = st.text_input("Class Name *", placeholder="CS-A")
                    fst = st.text_input("Fee Type *", placeholder="Tuition")
                with c2:
                    fsa = st.number_input("Amount (₹) *", 0.0, 100000.0, 5000.0, step=100.0)
                    fsf = st.selectbox("Frequency", ["monthly", "quarterly", "yearly", "one-time"])
                fsy = st.text_input("Academic Year", placeholder="2024-25")
                if st.form_submit_button("➕ Create", type="primary"):
                    if not fsc or not fst:
                        st.warning("Enter class and fee type")
                    else:
                        payload = {"class_name": fsc, "fee_type": fst,
                                   "amount": fsa, "frequency": fsf, "academic_year": fsy or None}
                        r = api_post("/fees/structure/create", json=payload)
                        if r and r.status_code == 200:
                            st.success("Created!")
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Failed"))

    with tab3:
        if user_role in ["admin", "teacher"]:
            st.markdown("### Record Payment")
            r = api_get("/students", params={"limit": 500})
            data = handle_response(r, show_error=False) if r else None
            students = data.get("students", []) if data else []
            if students:
                with st.form("record_payment"):
                    opts = {f"{s['name']} (ID {s['id']})": s["id"] for s in students}
                    sel_s = st.selectbox("Student *", list(opts.keys()))
                    c1, c2 = st.columns(2)
                    with c1:
                        pf = st.text_input("Fee Type *", placeholder="Tuition")
                        pa = st.number_input("Amount (₹) *", 0.0, 100000.0, 5000.0, step=100.0)
                    with c2:
                        pd = st.date_input("Payment Date")
                        pm = st.selectbox("Payment Method", ["cash", "card", "upi", "bank_transfer", "cheque"])
                    pstatus = st.selectbox("Status", ["paid", "pending"])
                    ptid = st.text_input("Transaction ID (optional)")
                    if st.form_submit_button("💰 Record Payment", type="primary"):
                        if not pf:
                            st.warning("Enter fee type")
                        else:
                            payload = {
                                "student_id": opts[sel_s], "fee_type": pf,
                                "amount": pa, "payment_date": pd.isoformat(),
                                "payment_method": pm, "status": pstatus,
                                "transaction_id": ptid or None,
                            }
                            r = api_post("/fees/payment/create", json=payload)
                            if r and r.status_code == 200:
                                st.success("Payment recorded!")
                                st.balloons()
                            else:
                                st.error(r.json().get("detail", "Failed"))




    with tab4:
        st.markdown("### ⏰ Fee Reminders")
        st.caption("Automated email reminders for pending fees. Runs daily at 9 AM UTC.")

        if user_role != "admin":
            st.info("Only admins can view and manage fee reminders.")
        else:
            # Action row
            _rm_c1, _rm_c2, _rm_c3 = st.columns([2, 2, 3])

            with _rm_c1:
                _rm_days = st.number_input(
                    "Days ahead",
                    min_value=1, max_value=30, value=2,
                    help="Include payments due within this many days",
                    key="fee_rm_days",
                )

            with _rm_c2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("🔍 Preview", use_container_width=True, key="fee_rm_preview_btn"):
                    _pr = api_get(f"/fees/reminders/preview?days_ahead={_rm_days}")
                    _pd = handle_response(_pr, show_error=False) if _pr else None
                    if _pd:
                        st.session_state["fee_rm_preview"] = _pd

            with _rm_c3:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("🚀 Run Reminders Now", type="primary", use_container_width=True, key="fee_rm_run_btn"):
                    with st.spinner("Sending reminders..."):
                        _rn = api_post(f"/fees/reminders/run-now?days_ahead={_rm_days}")
                        _rnd = handle_response(_rn, show_error=False) if _rn else None
                    if _rnd:
                        _s = _rnd.get("summary", {})
                        st.success(
                            f"✅ Done — sent: {_s.get('sent',0)}, "
                            f"skipped: {_s.get('skipped',0)}, "
                            f"failed: {_s.get('failed',0)}, "
                            f"total: {_s.get('total',0)}"
                        )
                        st.balloons()
                        st.session_state.pop("fee_rm_preview", None)

            # Preview results
            _prev = st.session_state.get("fee_rm_preview")
            if _prev:
                st.markdown("---")
                st.markdown(f"#### 📋 Preview (next {_prev.get('days_ahead', 0)} days)")
                _preview_payments = _prev.get("payments", [])
                if not _preview_payments:
                    st.info("No pending payments in this window — no reminders would be sent.")
                else:
                    import pandas as _pd
                    _pdf = _pd.DataFrame(_preview_payments)
                    st.caption(f"{len(_preview_payments)} payment(s) would receive a reminder")
                    st.dataframe(_pdf, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Reminder log
            st.markdown("#### 📜 Recent Reminders")
            _lg = api_get("/fees/reminders?limit=50")
            _lgd = handle_response(_lg, show_error=False) if _lg else None
            _logs = _lgd.get("reminders", []) if _lgd else []

            if not _logs:
                st.info("No reminders sent yet.")
            else:
                import pandas as _pd2
                _ldf = _pd2.DataFrame(_logs)
                _show_cols = ["sent_at", "student_name", "fee_type", "amount", "sent_to", "status", "error"]
                _avail = [c for c in _show_cols if c in _ldf.columns]
                st.dataframe(_ldf[_avail], use_container_width=True, hide_index=True)

                _counts = _ldf["status"].value_counts().to_dict() if "status" in _ldf.columns else {}
                _sc1, _sc2, _sc3 = st.columns(3)
                with _sc1:
                    st.metric("✅ Sent", _counts.get("sent", 0))
                with _sc2:
                    st.metric("⚠️ Skipped", _counts.get("skipped", 0))
                with _sc3:
                    st.metric("❌ Failed", _counts.get("failed", 0))
# ============================================================
# PAGE: CLASSES
# ============================================================
elif selected == t("classes"):
    st.markdown(f'<div class="main-header"><h1>{t("classes")}</h1><p>Cohort analytics</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Analytics", "➕ Create", "👥 Assign"])

    with tab1:
        r = api_get("/classes/list-names")
        names_data = handle_response(r, show_error=False) if r else None
        class_names = names_data.get("names", []) if names_data else []
        if not class_names:
            st.info("No classes yet")
        else:
            selected_class = st.selectbox("Select class", class_names)
            if st.button("📊 Load Analytics", type="primary"):
                r = api_get(f"/classes/{selected_class}/analytics")
                res = handle_response(r, show_error=False) if r else None
                if res and res.get("count", 0) > 0:
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: render_metric("👥", res["count"], "Students")
                    with c2: render_metric("📈", f"{res['average']:.1f}", "Average")
                    with c3: render_metric("🏆", f"{res['highest']:.1f}", "Highest")
                    with c4: render_metric("✅", f"{res['pass_rate']:.0f}%", "Pass Rate")

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### Top 3")
                        for s in res.get("top_3", []):
                            st.success(f"🥇 {s['name']} — {s['average']:.1f}%")
                    with c2:
                        st.markdown("### Bottom 3")
                        for s in res.get("bottom_3", []):
                            st.warning(f"⚠️ {s['name']} — {s['average']:.1f}%")

                    if res.get("grade_distribution"):
                        gdf = pd.DataFrame({"Grade": list(res["grade_distribution"].keys()),
                                            "Count": list(res["grade_distribution"].values())})
                        st.plotly_chart(style_chart(px.pie(gdf, values="Count", names="Grade", hole=0.4)),
                                      use_container_width=True)

                    if res.get("at_risk"):
                        st.markdown("### 🚨 At Risk")
                        st.dataframe(pd.DataFrame(res["at_risk"]), use_container_width=True)
                else:
                    st.info(res.get("message", "No data"))

    with tab2:
        st.markdown("### Create New Class")
        with st.form("create_class"):
            cn = st.text_input("Class Name *", placeholder="CS-A")
            cd = st.text_input("Department (optional)")
            if st.form_submit_button("➕ Create", type="primary"):
                if not cn:
                    st.warning("Enter class name")
                else:
                    r = api_post("/classes/create", json={"name": cn, "department": cd or None})
                    if r and r.status_code == 200:
                        st.success(f"Class '{cn}' created!")
                        time.sleep(0.5)
                        st.rerun()
                    elif r and r.status_code == 400:
                        st.warning(r.json().get("detail", "Error"))

    with tab3:
        st.markdown("### Assign Students to Class")
        r = api_get("/students", params={"limit": 500})
        data = handle_response(r, show_error=False) if r else None
        students = data.get("students", []) if data else []
        r2 = api_get("/classes/list-names")
        names_data = handle_response(r2, show_error=False) if r2 else None
        class_names = names_data.get("names", []) if names_data else []

        if students and class_names:
            target_class = st.selectbox("Target class", class_names)
            sel_students = st.multiselect("Select students",
                                         [f"{s['name']} (ID {s['id']})" for s in students])
            if st.button("👥 Assign", type="primary", use_container_width=True):
                if sel_students:
                    ids = [int(x.split("ID ")[1].rstrip(")")) for x in sel_students]
                    r = api_post("/classes/assign", json={"student_ids": ids, "class_name": target_class})
                    if r and r.status_code == 200:
                        st.success(r.json()["message"])


# ============================================================
# PAGE: PARENT LINKS
# ============================================================
elif selected == t("parent_links"):
    st.markdown(f'<div class="main-header"><h1>{t("parent_links")}</h1><p>Link parents to students</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔗 Link", "📋 All Links"])

    with tab1:
        r = api_get("/auth/users")
        users_data = handle_response(r, show_error=False) if r else None
        parents = [u for u in users_data["users"] if u["role"] == "parent"] if users_data else []
        r = api_get("/students", params={"limit": 500})
        students_data = handle_response(r, show_error=False) if r else None
        students = students_data.get("students", []) if students_data else []

        if not parents:
            st.warning("No parent accounts. Ask a parent to register first.")
        elif not students:
            st.warning("No students yet.")
        else:
            with st.form("link_form"):
                parent_opts = {f"{p['username']} ({p['email']})": p["id"] for p in parents}
                student_opts = {f"{s['name']} (ID {s['id']})": s["id"] for s in students}
                sel_parent = st.selectbox("Parent", list(parent_opts.keys()))
                sel_student = st.selectbox("Student", list(student_opts.keys()))
                rel = st.selectbox("Relationship", ["parent", "guardian", "mother", "father", "other"])
                if st.form_submit_button("🔗 Link", type="primary"):
                    r = api_post("/parents/link-child", json={
                        "parent_user_id": parent_opts[sel_parent],
                        "student_id": student_opts[sel_student],
                        "relationship": rel,
                    })
                    if r and r.status_code == 200:
                        st.success("Linked!")
                    else:
                        st.error(r.json().get("detail", "Failed"))

    with tab2:
        r = api_get("/parents/all-links")
        links_data = handle_response(r, show_error=False) if r else None
        links = links_data.get("links", []) if links_data else []
        if links:
            st.metric("Total Links", len(links))
            st.dataframe(pd.DataFrame(links), use_container_width=True)
            st.markdown("### 🔓 Unlink")
            link_opts = {f"{l['parent_username']} → {l['student_name']}": l["id"] for l in links}
            sel_link = st.selectbox("Select link", list(link_opts.keys()))
            if st.button("🗑️ Unlink", type="secondary"):
                r = api_delete(f"/parents/unlink/{link_opts[sel_link]}")
                if r and r.status_code == 200:
                    st.success("Unlinked!")
                    st.rerun()
        else:
            st.info("No links yet")


# ============================================================
# PAGE: PROFILE
# ============================================================
# ============================================================
# PAGE: STUDENT PROFILE
# ============================================================
elif selected == t("profile"):
    st.markdown(f'<div class="main-header"><h1>{t("profile")}</h1><p>Complete student profile with photo</p></div>', unsafe_allow_html=True)

    r = api_get("/students", params={"limit": 500})
    data = handle_response(r, show_error=False) if r else None
    students = data.get("students", []) if data else []

    if not students:
        st.info("No students yet")
    else:
        opts = {f"{s['name']} (ID {s['id']})": s["id"] for s in students}
        sel = st.selectbox("Select student", list(opts.keys()), key="profile_sel")
        sid = opts[sel]

        # Auto-load if we have a loaded profile for this student in session
        cached = st.session_state.get("profile_cache", {})
        if str(sid) in cached:
            prof = cached[str(sid)]
        else:
            prof = None

        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("👁️ Load Profile", type="primary", use_container_width=True):
                r = api_get(f"/students/{sid}/profile")
                prof = handle_response(r, show_error=False) if r else None
                if prof:
                    st.session_state.profile_cache = st.session_state.get("profile_cache", {})
                    st.session_state.profile_cache[str(sid)] = prof
                    st.rerun()
        with col_b:
            if prof:
                if st.button("🔄 Reload", use_container_width=True):
                    st.session_state.profile_cache.pop(str(sid), None)
                    st.rerun()

        if not prof:
            st.info("Click **👁️ Load Profile** to view details")
        else:
            s = prof["student"]

            # ---- Header with photo ----
                      # ---- Header with photo (robust display + avatar fallback) ----
            c1, c2 = st.columns([1, 3])
            with c1:
                photo_url = get_student_photo_url(s.get("photo_url"))

                # ---------- Helper: render photo bytes or a styled avatar ----------
                def _render_photo_or_avatar(url, name: str):
                    """Show the photo if loadable & non-degenerate; else show initial avatar."""
                    initials = "".join(
                        part[0].upper() for part in (name or "?").split()[:2]
                    ) or "?"

                    avatar_html = f"""
                        <div style="width: 150px; height: 150px; border-radius: 16px;
                                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                                    display: flex; align-items: center; justify-content: center;
                                    color: #ffffff; font-size: 3rem; font-weight: 700;
                                    letter-spacing: 0.05em;
                                    box-shadow: 0 6px 20px rgba(99,102,241,0.25);
                                    margin-bottom: 0.5rem;">
                            {initials}
                        </div>
                    """

                    if not url:
                        st.markdown(avatar_html, unsafe_allow_html=True)
                        st.caption("No photo uploaded")
                        return

                    # Cache-buster so re-uploads appear immediately
                    sep = "&" if "?" in url else "?"
                    fetch_url = f"{url}{sep}t={int(datetime.now().timestamp())}"

                    try:
                        img_resp = requests.get(fetch_url, timeout=6)
                    except Exception as _e:
                        st.markdown(avatar_html, unsafe_allow_html=True)
                        st.caption(f"⚠️ Photo load failed: {type(_e).__name__}")
                        return

                    if img_resp.status_code != 200 or not img_resp.content:
                        st.markdown(avatar_html, unsafe_allow_html=True)
                        st.caption(f"⚠️ Photo unavailable (HTTP {img_resp.status_code})")
                        return

                    img_bytes = img_resp.content

                    # Detect degenerate (e.g. 1×1) images when Pillow is available
                    try:
                        from PIL import Image as _PILImage
                        _im = _PILImage.open(io.BytesIO(img_bytes))
                        _w, _h = _im.size
                        if _w <= 2 or _h <= 2:
                            st.markdown(avatar_html, unsafe_allow_html=True)
                            st.caption("⚠️ Uploaded image is too small — please upload a real photo")
                            return
                    except Exception:
                        # PIL missing or image not parseable — just try to render it
                        pass

                    st.image(img_bytes, width=150, caption=name)

                _render_photo_or_avatar(photo_url, s["name"])

                # ---- Photo upload ----
                if user_role in ["admin", "teacher"]:
                    uploaded = st.file_uploader(
                        "Upload Photo",
                        type=["jpg", "jpeg", "png", "webp"],
                        key=f"photo_up_{sid}",
                    )
                    if uploaded:
                        with st.spinner("Uploading..."):
                            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                            r = api_post(f"/students/{sid}/photo", files=files)
                        if r and r.status_code == 200:
                            st.success("✅ Photo uploaded!")
                            # Clear cache to force reload
                            if "profile_cache" in st.session_state:
                                st.session_state.profile_cache.pop(str(sid), None)
                            time.sleep(0.8)
                            st.rerun()
                        else:
                            try:
                                err = r.json().get("detail", "Unknown error")
                            except Exception:
                                err = r.text[:200] if r else "No response"
                            st.error(f"❌ Upload failed: {err}")

                    if photo_url:
                        if st.button("🗑️ Delete Photo", key=f"del_photo_{sid}"):
                            r = api_delete(f"/students/{sid}/photo")
                            if r and r.status_code == 200:
                                if "profile_cache" in st.session_state:
                                    st.session_state.profile_cache.pop(str(sid), None)
                                st.success("Deleted")
                                time.sleep(0.5)
                                st.rerun()

            with c2:
                st.markdown(f"## {s['name']}")
                st.markdown(f"**ID:** {s['id']} | **Class:** {s.get('class_name', 'N/A')} | **Dept:** {s.get('department', 'N/A')}")

                c_a, c_b, c_c, c_d = st.columns(4)
                with c_a: st.metric("📊 Average", f"{s['average']:.1f}%")
                with c_b: st.metric("🏆 Grade", s["grade"])
                with c_c: st.metric("📈 Total", f"{s['total_marks']:.0f}")
                with c_d: st.metric("📚 Subjects", len(s.get("subjects", [])))
            st.markdown("---")

            # Edit profile
            if user_role in ["admin", "teacher"]:
                with st.expander("✏️ Edit Profile Details"):
                    with st.form(f"edit_profile_{sid}"):
                        em = st.text_input("Email", value=s.get("email") or "")
                        ph = st.text_input("Phone", value=s.get("phone") or "")
                        dob = st.text_input("Date of Birth (YYYY-MM-DD)", value=s.get("date_of_birth") or "")
                        addr = st.text_area("Address", value=s.get("address") or "")
                        if st.form_submit_button("💾 Save"):
                            payload = {
                                "email": em or None, "phone": ph or None,
                                "date_of_birth": dob or None, "address": addr or None,
                            }
                            r = api_put(f"/students/{sid}/profile", json=payload)
                            if r and r.status_code == 200:
                                if "profile_cache" in st.session_state:
                                    st.session_state.profile_cache.pop(str(sid), None)
                                st.success("Updated!")
                                time.sleep(0.5)
                                st.rerun()

            # Subject chart
            if s.get("subjects") and s.get("marks"):
                st.markdown("### 📚 Subject-wise Performance")
                df = pd.DataFrame({"Subject": s["subjects"], "Marks": s["marks"]})
                fig = px.bar(df, x="Subject", y="Marks", color="Marks",
                             color_continuous_scale="RdYlGn", text="Marks")
                fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig.update_layout(yaxis_range=[0, 105], showlegend=False)
                st.plotly_chart(style_chart(fig), use_container_width=True)

            # Attendance summary
            st.markdown("### 📅 Attendance Summary")
            att = prof.get("attendance", {})
            if att:
                total_att = sum(att.values())
                present = att.get("Present", 0)
                rate = (present / total_att * 100) if total_att > 0 else 0
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: st.metric("Total", total_att)
                with c2: st.metric("Present", present)
                with c3: st.metric("Absent", att.get("Absent", 0))
                with c4: st.metric("Late", att.get("Late", 0))
                with c5: st.metric("Rate", f"{rate:.1f}%")
                st.progress(rate / 100)
            else:
                st.info("No attendance records")

            # Heatmap
            st.markdown("### 🔥 Attendance Heatmap")
            r = api_get(f"/attendance/{sid}/heatmap")
            hdata = handle_response(r, show_error=False) if r else None
            if hdata and hdata.get("heatmap"):
                hm = hdata["heatmap"]
                if hm:
                    hm_df = pd.DataFrame(hm)
                    hm_df["date"] = pd.to_datetime(hm_df["date"])
                    fig = px.scatter(
                        hm_df, x="date", y=[1] * len(hm_df),
                        color="status",
                        color_discrete_map={"present": "#10b981", "partial": "#f59e0b", "absent": "#ef4444"},
                        size=[20] * len(hm_df),
                        hover_data=["date", "count", "score"]
                    )
                    fig.update_yaxes(showticklabels=False)
                    fig.update_layout(height=150, showlegend=True)
                    st.plotly_chart(style_chart(fig), use_container_width=True)
                else:
                    st.info("No attendance data for heatmap")
            else:
                st.info("No heatmap data")

            # Trends
            if prof.get("trends"):
                st.markdown("### 📉 Performance Trends")
                tdf = pd.DataFrame(prof["trends"])
                if "created_at" in tdf.columns and "average" in tdf.columns:
                    tdf["created_at"] = pd.to_datetime(tdf["created_at"])
                    fig = px.line(tdf, x="created_at", y="average", markers=True)
                    st.plotly_chart(style_chart(fig), use_container_width=True)



            # ============================================================
            # BEHAVIOR NOTES (Feature 5)
            # ============================================================
            st.markdown("---")
            st.markdown("### 📝 Behavior Notes")
            st.caption("Private notes about this student. Teachers and admins can add notes; parents see only notes marked as visible.")

            # Fetch notes
            _notes_resp = api_get(f"/students/{sid}/notes")
            _notes_data = handle_response(_notes_resp, show_error=False) if _notes_resp else None
            _all_notes = _notes_data.get("notes", []) if _notes_data else []

            # Filter + add row
            _note_tabs = st.tabs(["📋 View Notes", "➕ Add Note"])

            with _note_tabs[0]:
                if not _all_notes:
                    st.info("No notes yet for this student.")
                else:
                    # Filter
                    _filter_col, _ = st.columns([2, 3])
                    with _filter_col:
                        _type_filter = st.selectbox(
                            "Filter by type",
                            options=["All", "positive", "concern", "incident", "observation"],
                            key=f"notes_filter_{sid}",
                        )

                    _type_icons = {
                        "positive": ("🟢", "#10b981"),
                        "concern": ("🟠", "#f59e0b"),
                        "incident": ("🔴", "#ef4444"),
                        "observation": ("🔵", "#3b82f6"),
                    }

                    _shown = 0
                    for _note in _all_notes:
                        if _type_filter != "All" and _note.get("note_type") != _type_filter:
                            continue
                        _shown += 1
                        _ntype = _note.get("note_type", "observation")
                        _icon, _color = _type_icons.get(_ntype, ("⚪", "#6b7280"))
                        _author = _note.get("author_name") or "Unknown"
                        _created = (_note.get("created_at") or "")[:16]
                        _is_public = bool(_note.get("visible_to_parents"))
                        _visibility_badge = (
                            '<span style="background:#10b98122;color:#10b981;'
                            'padding:0.15rem 0.5rem;border-radius:6px;font-size:0.7rem;'
                            'font-weight:600;margin-left:0.5rem;">👁 Visible to parents</span>'
                            if _is_public else
                            '<span style="background:#6b728022;color:#6b7280;'
                            'padding:0.15rem 0.5rem;border-radius:6px;font-size:0.7rem;'
                            'font-weight:600;margin-left:0.5rem;">🔒 Private</span>'
                        )

                        _note_id = _note.get("id")
                        _can_delete = user_role == "admin" or _note.get("author_id") == user["id"]

                        st.markdown(
                            f"""
                            <div style="border-left:4px solid {_color};
                                        background:{_color}0F;
                                        padding:0.75rem 1rem;
                                        border-radius:8px;
                                        margin-bottom:0.5rem;">
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <div>
                                        <b style="color:{_color};">{_icon} {_ntype.title()}</b>
                                        <span style="color:#6b7280;font-size:0.85rem;margin-left:0.5rem;">
                                            — {_author} · {_created}
                                        </span>
                                        {_visibility_badge}
                                    </div>
                                </div>
                                <div style="margin-top:0.5rem;color:inherit;">{_note.get('content', '')}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        if _can_delete:
                            _dc1, _dc2, _ = st.columns([1, 1, 8])
                            with _dc1:
                                if st.button("🗑️ Delete", key=f"del_note_{_note_id}", use_container_width=True):
                                    _dr = api_delete(f"/students/{sid}/notes/{_note_id}")
                                    if _dr and _dr.status_code == 200:
                                        st.success("Deleted")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete")
                            with _dc2:
                                st.markdown(
                                    f'<small style="color:#6b7280;">ID: {_note_id}</small>',
                                    unsafe_allow_html=True,
                                )

                    if _shown == 0:
                        st.info(f"No '{_type_filter}' notes found.")

            with _note_tabs[1]:
                if user_role not in ("admin", "teacher"):
                    st.warning("Only admins and teachers can add behavior notes.")
                else:
                    with st.form(f"add_note_form_{sid}", clear_on_submit=True):
                        _new_type = st.selectbox(
                            "Note type",
                            options=["positive", "concern", "incident", "observation"],
                            index=3,
                            key=f"new_note_type_{sid}",
                        )
                        _new_content = st.text_area(
                            "Note",
                            height=120,
                            placeholder="Describe the observation...",
                            key=f"new_note_content_{sid}",
                        )
                        _new_visible = st.checkbox(
                            "Make visible to parents",
                            value=False,
                            key=f"new_note_visible_{sid}",
                        )
                        _submit = st.form_submit_button("➕ Add Note", type="primary", use_container_width=True)

                        if _submit:
                            if not _new_content or len(_new_content.strip()) < 2:
                                st.error("Note content is too short.")
                            else:
                                _payload = {
                                    "note_type": _new_type,
                                    "content": _new_content.strip(),
                                    "visible_to_parents": bool(_new_visible),
                                }
                                _ar = api_post(f"/students/{sid}/notes", json=_payload)
                                if _ar and _ar.status_code == 200:
                                    st.success("✅ Note added!")
                                    st.rerun()
                                else:
                                    try:
                                        _err = _ar.json().get("detail", "Failed")
                                    except Exception:
                                        _err = "Unknown error"
                                    st.error(f"❌ {_err}")




            # ============================================================
            # ACHIEVEMENT BADGES (Feature 6)
            # ============================================================
            st.markdown("---")
            st.markdown("### 🏅 Achievement Badges")

            _bdg_resp = api_get(f"/students/{sid}/badges")
            _bdg_data = handle_response(_bdg_resp, show_error=False) if _bdg_resp else None
            _earned = _bdg_data.get("badges", []) if _bdg_data else []

            if not _earned:
                st.info("No badges earned yet. Keep up the good work!")
            else:
                _earned_cols = st.columns(min(len(_earned), 6))
                for _idx, _b in enumerate(_earned[:6]):
                    with _earned_cols[_idx]:
                        st.markdown(
                            f"""
                            <div style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%);
                                        border-radius:14px;padding:1rem;text-align:center;
                                        color:white;box-shadow:0 4px 12px rgba(99,102,241,0.2);
                                        height:120px;">
                                <div style="font-size:2.2rem;line-height:1;">{_b.get('icon','🏅')}</div>
                                <div style="font-weight:600;font-size:0.85rem;margin-top:0.4rem;">{_b.get('name','')}</div>
                                <div style="font-size:0.7rem;opacity:0.8;margin-top:0.2rem;">{_b.get('awarded_at','')[:10]}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Admin: award badge tool
            if user_role == "admin":
                with st.expander("➕ Award a badge"):
                    _all_bdg_resp = api_get("/badges/all")
                    _all_bdg_data = handle_response(_all_bdg_resp, show_error=False) if _all_bdg_resp else None
                    _all_badges = _all_bdg_data.get("badges", []) if _all_bdg_data else []
                    if _all_badges:
                        _earned_codes = {b.get("achievement_code") for b in _earned}
                        _available = [b for b in _all_badges if b["code"] not in _earned_codes]
                        if not _available:
                            st.success("Student has earned all available badges!")
                        else:
                            _opts = {f"{b.get('icon','🏅')} {b['name']}": b["code"] for b in _available}
                            _sel = st.selectbox("Select badge", options=list(_opts.keys()), key=f"award_{sid}")
                            if st.button("🏅 Award Badge", type="primary", key=f"award_btn_{sid}"):
                                _resp = api_post("/badges/award", json={"student_id": sid, "code": _opts[_sel]})
                                if _resp and _resp.status_code == 200:
                                    st.success("Badge awarded!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    try:
                                        _err = _resp.json().get("detail", "Failed")
                                    except Exception:
                                        _err = "Unknown error"
                                    st.error(f"Failed: {_err}")
                    else:
                        st.info("No badge definitions available.")

            # Parents
            if prof.get("parents"):
                st.markdown("### 👨‍👩‍👧 Linked Parents")
                st.dataframe(pd.DataFrame(prof["parents"]), use_container_width=True)

            # PDF download
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                pdf_tpl = st.selectbox("PDF Template", ["classic", "modern", "minimal"], key="profile_tpl")
            with c2:
                if st.button("📄 Download PDF Report", use_container_width=True):
                    endpoint = (f"/students/{sid}/report-card"
                                if pdf_tpl == "classic"
                                else f"/students/{sid}/report-card/{pdf_tpl}")
                    r = api_get(endpoint)
                    if r and r.status_code == 200:
                        st.download_button("💾 Save PDF", data=r.content,
                                          file_name=f"report_{sid}_{pdf_tpl}.pdf",
                                          mime="application/pdf")

# ============================================================
# PAGE: SAVED FILTERS
# ============================================================
elif selected == t("filters"):
    st.markdown(f'<div class="main-header"><h1>{t("filters")}</h1><p>Save and reuse filter presets</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 My Filters", "➕ Create"])

    with tab1:
        r = api_get("/filters")
        data = handle_response(r, show_error=False) if r else None
        filters = data.get("filters", []) if data else []
        if filters:
            st.metric("Saved Filters", len(filters))
            for f in filters:
                with st.expander(f"🔍 {f['name']} ({f['entity']})"):
                    try:
                        st.json(json.loads(f["filter_json"]))
                    except Exception:
                        st.code(f["filter_json"])
                    if f.get("user_id") == user["id"]:
                        if st.button(f"🗑️ Delete", key=f"del_{f['id']}"):
                            r = api_delete(f"/filters/{f['id']}")
                            if r and r.status_code == 200:
                                st.success("Deleted")
                                st.rerun()
        else:
            st.info("No saved filters yet")

    with tab2:
        st.markdown("### Create Filter Preset")
        with st.form("save_filter"):
            fn = st.text_input("Filter Name *", placeholder="High Performers")
            fe = st.selectbox("Entity", ["students", "users"])
            fj = st.text_area("Filter JSON *", placeholder='{"grade": "A+", "min_average": 90}')
            fs = st.checkbox("Share with all users")
            if st.form_submit_button("💾 Save Filter", type="primary"):
                if not fn or not fj:
                    st.warning("Enter name and filter data")
                else:
                    try:
                        json.loads(fj)
                        r = api_post("/filters/save", json={
                            "name": fn, "entity": fe,
                            "filter_json": fj, "is_shared": fs,
                        })
                        if r and r.status_code == 200:
                            st.success("Filter saved!")
                            time.sleep(0.5)
                            st.rerun()
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format")


# ============================================================
# PAGE: LIVE FEED
# ============================================================
# ============================================================
# PAGE: LIVE FEED
# ============================================================
elif selected == t("live"):
    st.markdown(f'<div class="main-header"><h1>{t("live")}</h1><p>Real-time activity feed</p></div>', unsafe_allow_html=True)

    # ---- Auto-refresh controls ----
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        auto_refresh = st.toggle("🔄 Auto-refresh (every 10s)", value=True, key="live_auto")
    with c2:
        manual_refresh = st.button("🔃 Refresh Now", use_container_width=True)
    with c3:
        if user_role == "admin":
            if st.button("📡 Broadcast Test", use_container_width=True):
                r = api_get("/live/test-broadcast")
                if r and r.status_code == 200:
                    st.success("Broadcast sent!")
                    time.sleep(0.5)
                    st.rerun()
        else:
            if st.button("📡 Send Test Event", use_container_width=True):
                r = api_get("/ws/test")
                if r and r.status_code == 200:
                    st.success("Test event sent!")
                    time.sleep(0.5)
                    st.rerun()

    # ---- Stats ----
    r = api_get("/live/stats")
    stats = handle_response(r, show_error=False) if r else None

    if stats:
        c1, c2 = st.columns([1, 3])
        with c1:
            render_metric("📊", stats.get("total", 0), "Total Events")
        with c2:
            if stats.get("by_type"):
                st.markdown("**Event Types:**")
                type_cols = st.columns(min(len(stats["by_type"]), 6))
                for i, (evt, cnt) in enumerate(list(stats["by_type"].items())[:6]):
                    with type_cols[i % 6]:
                        st.metric(evt.replace("_", " ").title(), cnt)

    st.markdown("---")

    # ---- Events list ----
    st.markdown("### 📋 Recent Events")

    # Track last seen event id for incremental fetch
    last_id = st.session_state.get("live_last_id", 0)

    r = api_get("/live/events", params={"since_id": 0, "limit": 30})
    data = handle_response(r, show_error=False) if r else None

    if not data or not data.get("events"):
        st.info("No live events yet. Trigger one using the test button above, or perform an action (create student, upload photo, etc.)")
    else:
        events = data["events"]
        # Update last seen id
        max_id = max(e["id"] for e in events)
        st.session_state.live_last_id = max_id

        st.caption(f"Showing {len(events)} most recent events (auto-updates every 10s)")

        # Event type → icon + color mapping
        event_meta = {
            "student_created": ("👤", "#10b981", "New Student"),
            "photo_uploaded": ("📸", "#3b82f6", "Photo Upload"),
            "exam_created": ("📅", "#8b5cf6", "Exam Created"),
            "assignment_created": ("📝", "#f59e0b", "Assignment"),
            "fee_paid": ("💰", "#10b981", "Fee Payment"),
            "ml_trained": ("🤖", "#667eea", "ML Training"),
            "broadcast_test": ("📢", "#dc2626", "Broadcast"),
            "test": ("🧪", "#6b7280", "Test Event"),
        }

        for e in events:
            icon, color, label = event_meta.get(e["event_type"], ("📌", "#6b7280", e["event_type"]))
            payload = e.get("payload", {})

            # Build details line
            details = []
            for k, v in payload.items():
                if isinstance(v, (str, int, float, bool)):
                    details.append(f"**{k}:** {v}")
            details_str = " | ".join(details) if details else ""

            # Time formatting
            try:
                event_time = e["created_at"]
                if isinstance(event_time, str):
                    event_time_str = event_time[:19]
                else:
                    event_time_str = str(event_time)[:19]
            except Exception:
                event_time_str = "unknown"

            st.markdown(f"""
            <div style="background: rgba(99,102,241,0.05);
                        border-left: 3px solid {color};
                        padding: 0.75rem 1rem;
                        border-radius: 8px;
                        margin: 0.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.1rem;">{icon}</span>
                        <b style="margin-left: 0.5rem;">{label}</b>
                    </div>
                    <small style="color: #6b7280;">{event_time_str}</small>
                </div>
                <div style="margin-top: 0.25rem; font-size: 0.85rem; color: #4b5563;">
                    {details_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ---- Auto refresh logic ----
    if auto_refresh and not manual_refresh:
        time.sleep(10)
        st.rerun()

    # ---- Documentation expander ----
    with st.expander("📖 How WebSocket Works"):
        st.markdown("""
        **Backend WebSocket endpoint:** `ws://localhost:8000/ws/notifications?token=YOUR_JWT`

        **Events emitted automatically:**
        - `student_created` — New student saved
        - `photo_uploaded` — Student photo uploaded
        - `exam_created` — Exam scheduled
        - `assignment_created` — Assignment created
        - `fee_paid` — Fee payment recorded
        - `ml_trained` — ML model retrained
        - `broadcast_test` — Admin broadcast (all users)

        **How this page works:**
        - Uses **polling** (every 10 seconds) instead of WebSocket because Streamlit doesn't support persistent WebSocket connections.
        - Fetches events from `GET /live/events`.
        - Auto-refresh can be toggled off at the top.

        **Python client example:**
        ```python
        import asyncio, websockets, json

        async def listen():
            uri = "ws://localhost:8000/ws/notifications?token=YOUR_TOKEN"
            async with websockets.connect(uri) as ws:
                while True:
                    msg = await ws.recv()
                    print(json.loads(msg))

        asyncio.run(listen())
""")

# ============================================================
# PAGE: NOTIFICATIONS
# ============================================================
elif selected == t("notifications"):
    st.markdown(f'<div class="main-header"><h1>{t("notifications")}</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("✅ Mark All Read", use_container_width=True):
            api_put("/notifications/mark-all-read")
            st.rerun()
    r = api_get("/notifications", params={"limit": 100})
    data = handle_response(r, show_error=False) if r else None
    if data:
        st.info(f"Total: {data['count']} | Unread: {data['unread_count']}")
        for n in data.get("notifications", []):
            icon = {"Achievement": "🏆", "Warning": "⚠️", "Success": "✅", "Info": "ℹ️"}.get(n["type"], "📌")
            st.markdown(f"{'🔵' if not n['is_read'] else '⚪'} {icon} {n['type']} — {n['message']}")
            st.caption(n["created_at"])
            st.divider()


# ============================================================
# PAGE: SCHEDULED REPORTS (Feature 3)
# ============================================================
elif selected == t("scheduled_reports"):
    st.markdown(f'<div class="main-header"><h1>{t("scheduled_reports")}</h1><p>Automated email reports</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Scheduled", "🕒 Upcoming", "➕ Add New"])

    with tab1:
        r = api_get("/reports/scheduled")
        data = handle_response(r, show_error=False) if r else None
        reports = data.get("reports", []) if data else []
        if reports:
            st.metric("Active Reports", len([x for x in reports if x.get("enabled")]))
            st.dataframe(pd.DataFrame(reports), use_container_width=True)
            st.markdown("### 🗑️ Delete Report")
            opts = {f"{r_['report_type']} → {r_['recipients']}": r_["id"] for r_ in reports}
            sel = st.selectbox("Select report", list(opts.keys()))
            if st.button("🗑️ Delete", type="secondary"):
                r = api_delete(f"/reports/scheduled/{opts[sel]}")
                if r and r.status_code == 200:
                    st.success("Deleted")
                    st.rerun()
        else:
            st.info("No scheduled reports yet")

    with tab2:
        st.markdown("### 🕒 Upcoming Report Runs")
        r = api_get("/reports/upcoming")
        data = handle_response(r, show_error=False) if r else None
        if data and data.get("count", 0) > 0:
            st.metric("Upcoming", data["count"])
            for u in data["upcoming"]:
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 0.75rem;">
                    <h4 style="margin: 0;">📧 {u['report_type'].title()}</h4>
                    <p style="margin: 0.25rem 0;"><b>To:</b> {u['recipients']}</p>
                    <p style="margin: 0.25rem 0;"><b>Schedule:</b> {u['schedule']}</p>
                    <p style="margin: 0.25rem 0;"><b>Next run:</b> {u['next_run'][:19]}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming reports. Create one in the Add New tab.")

    with tab3:
        st.markdown("### Create Scheduled Report")
        st.caption("Reports are sent every 7 days automatically")
        with st.form("create_report"):
            rt = st.selectbox("Report Type", ["weekly_summary", "performance", "attendance"])
            rr = st.text_input("Recipients (comma-separated emails) *",
                               placeholder="admin@school.com, principal@school.com")
            rs = st.selectbox("Schedule", ["weekly", "daily", "monthly"])
            re = st.checkbox("Enable", value=True)
            if st.form_submit_button("➕ Create Report", type="primary"):
                if not rr:
                    st.warning("Enter recipient emails")
                else:
                    r = api_post("/reports/schedule", json={
                        "report_type": rt, "recipients": rr,
                        "schedule": rs, "enabled": re,
                    })
                    if r and r.status_code == 200:
                        st.success("Scheduled!")
                        st.rerun()


# ============================================================
# PAGE: BACKUP
# ============================================================
elif selected == t("backup"):
    st.markdown(f'<div class="main-header"><h1>{t("backup")}</h1><p>Database backup & restore</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💾 Create Backup", "📋 History"])

    with tab1:
        st.markdown("### Create Manual Backup")
        st.info("Backups include the database and all uploaded photos.")
        if st.button("💾 Create Backup Now", type="primary", use_container_width=True):
            with st.spinner("Creating backup..."):
                r = api_post("/backup/create")
                if r and r.status_code == 200:
                    d = r.json()
                    st.success(f"✅ Backup created: {d['filename']} ({d['size_mb']} MB)")
                    st.balloons()
                else:
                    st.error(r.json().get("detail", "Failed"))

        st.markdown("---")
        st.markdown("### 🤖 Auto Backups")
        st.caption("Automatic backups run every 24 hours, keeping the last 7 backups")
        r = api_get("/backup/auto-list")
        auto = handle_response(r, show_error=False) if r else None
        if auto and auto.get("backups"):
            st.metric("Auto Backups", len(auto["backups"]))
            st.dataframe(pd.DataFrame(auto["backups"]), use_container_width=True)

    with tab2:
        st.markdown("### Backup History")
        r = api_get("/backup/list")
        data = handle_response(r, show_error=False) if r else None
        backups = data.get("backups", []) if data else []
        if backups:
            st.metric("Total Backups", len(backups))
            for b in backups:
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"{b['filename']} — {round(b.get('size_bytes', 0) / 1024 / 1024, 2)} MB")
                    st.caption(f"{b.get('created_at', 'N/A')} | Type: {b.get('backup_type', 'manual')}")
                with c2:
                    if st.button("📥 Download", key=f"dl_{b['id']}"):
                        r = api_get(f"/backup/download/{b['filename']}")
                        if r and r.status_code == 200:
                            st.download_button("💾 Save", data=r.content,
                                               file_name=b["filename"],
                                               mime="application/zip",
                                               key=f"dl_btn_{b['id']}")
                st.divider()
        else:
            st.info("No backups yet")


# ============================================================
# PAGE: PDF TEMPLATES
# ============================================================
elif selected == t("pdf_templates"):
    st.markdown(f'<div class="main-header"><h1>{t("pdf_templates")}</h1><p>Choose PDF report card styles</p></div>', unsafe_allow_html=True)

    st.markdown("### 🎨 Available Templates")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">📄</div>
            <h3>Classic</h3>
            <p>Original simple layout</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">🎨</div>
            <h3>Modern</h3>
            <p>Colorful with grade badges</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <h3>Minimal</h3>
            <p>Clean and simple</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📥 Generate Report Card")
    r = api_get("/students", params={"limit": 500})
    data = handle_response(r, show_error=False) if r else None
    students = data.get("students", []) if data else []

    if students:
        c1, c2 = st.columns(2)
        with c1:
            opts = {f"{s['name']} (ID {s['id']})": s["id"] for s in students}
            sel = st.selectbox("Student", list(opts.keys()))
        with c2:
            tpl = st.selectbox("Template", ["classic", "modern", "minimal"])
        if st.button("📄 Generate PDF", type="primary", use_container_width=True):
            sid = opts[sel]
            endpoint = f"/students/{sid}/report-card" if tpl == "classic" else f"/students/{sid}/report-card/{tpl}"
            r = api_get(endpoint)
            if r and r.status_code == 200:
                st.download_button("💾 Download PDF", data=r.content,
                                   file_name=f"report_{sid}_{tpl}.pdf",
                                   mime="application/pdf")


# ============================================================
# PAGE: ML INSIGHTS
# ============================================================
elif selected == t("ml"):
    st.markdown(f'<div class="main-header"><h1>{t("ml")}</h1><p>AI-powered grade prediction and at-risk detection</p></div>', unsafe_allow_html=True)

    r = api_get("/ml/status")
    status = handle_response(r, show_error=False) if r else None

    if not status:
        st.error("Cannot reach ML endpoints. Is the backend running?")
    elif not status.get("available"):
        st.error("❌ scikit-learn not installed on backend")
        st.code("pip install scikit-learn joblib numpy")
    else:
        meta = status.get("meta", {})
        c1, c2, c3 = st.columns(3)
        with c1:
            if status.get("trained"):
                st.success("✅ Model Trained")
            else:
                st.warning("⚠️ Model Not Trained")
        with c2:
            st.metric("Training Samples", meta.get("samples", 0))
        with c3:
            if meta.get("grade_r2"):
                st.metric("Model R²", f"{meta['grade_r2']:.2f}")

        if status.get("trained") and meta.get("trained_at"):
            st.caption(f"Last trained: {meta['trained_at'][:19]} UTC")

        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["🎯 Predict", "🚨 At-Risk", "🔄 Train Model"])

        with tab1:
            st.markdown("### Predict Student's Next Score")
            r = api_get("/students", params={"limit": 500})
            data = handle_response(r, show_error=False) if r else None
            students = data.get("students", []) if data else []

            if not students:
                st.info("No students yet.")
            else:
                opts = {f"{s['name']} (ID {s['id']})": s["id"] for s in students}
                sel = st.selectbox("Select student", list(opts.keys()), key="ml_predict_sel")
                sid = opts[sel]

                if st.button("🔮 Predict Next Score", type="primary", use_container_width=True):
                    r = api_get(f"/ml/predict/{sid}")
                    res = handle_response(r, show_error=False) if r else None
                    if not res:
                        st.error("Prediction failed")
                    elif "error" in res.get("prediction", {}):
                        st.warning(res["prediction"]["error"])
                    else:
                        pred = res["prediction"]
                        risk = res["risk"]
                        c1, c2, c3, c4 = st.columns(4)
                        with c1: render_metric("🎯", f"{pred['predicted_score']}%", "Predicted")
                        with c2: render_metric("📊", f"{pred['current_average']}%", "Current")
                        with c3:
                            trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(pred["trend"], "❓")
                            render_metric(trend_icon, pred["trend"].title(), "Trend")
                        with c4:
                            risk_pct = int(risk["probability"] * 100)
                            render_metric("⚠️" if risk["at_risk"] else "✅", f"{risk_pct}%", "Risk")
                        st.markdown(f"**Confidence range:** {pred['confidence_low']}% – {pred['confidence_high']}%")
                        if res.get("recommendations"):
                            st.markdown("### 💡 Recommendations")
                            for rec in res["recommendations"]:
                                st.markdown(f'<div class="recommendation-card">{rec}</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown("### Students At Risk")
            st.caption("Students flagged by the ML model as likely to struggle")
            if st.button("🔍 Find At-Risk Students", type="primary", use_container_width=True):
                r = api_get("/ml/at-risk")
                res = handle_response(r, show_error=False) if r else None
                if not res:
                    st.error("Failed to load")
                elif res["count"] == 0:
                    st.success("🎉 No at-risk students detected!")
                else:
                    st.error(f"⚠️ {res['count']} student(s) at risk")
                    df = pd.DataFrame(res["students"])
                    df["probability"] = df["probability"].apply(lambda x: f"{x*100:.0f}%")
                    st.dataframe(df, use_container_width=True)

        with tab3:
            st.markdown("### Train the Model")
            st.caption("Trains on all students with marks data. Needs at least 5 students.")
            if user_role not in ["admin", "teacher"]:
                st.info("Only admins and teachers can train the model.")
            else:
                st.warning("⚠️ Training will overwrite the existing model.")
                if st.button("🚀 Train Model Now", type="primary", use_container_width=True):
                    with st.spinner("Training... (5-10 seconds)"):
                        r = api_post("/ml/train")
                        res = handle_response(r, show_error=False) if r else None
                    if not res:
                        st.error("Training failed")
                    elif res.get("error"):
                        st.error(res["error"])
                        if res.get("hint"):
                            st.info(res["hint"])
                    elif res.get("ok"):
                        st.success("✅ Model trained!")
                        st.balloons()
                        c1, c2, c3 = st.columns(3)
                        with c1: st.metric("Samples", res["samples"])
                        with c2: st.metric("Grade MAE", f"±{res['grade_mae']}%")
                        with c3: st.metric("R² Score", f"{res['grade_r2']:.2f}")
                        time.sleep(1)
                        st.rerun()


# ============================================================
# PAGE: SETTINGS (NEW — Theme + Notifications + Language)
# ============================================================
elif selected == t("settings"):
    st.markdown(f'<div class="main-header"><h1>{t("settings")}</h1><p>Preferences and account settings</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🎨 Appearance", "🔔 Notifications", "🔒 Account"])

    with tab1:
        st.markdown("### 🎨 Theme")
        st.caption("Your choice is saved to your account and persists across sessions.")
        theme_choice = st.radio("Choose theme",
                                ["light", "dark"],
                                index=0 if st.session_state.theme == "light" else 1,
                                format_func=lambda x: "☀️ Light" if x == "light" else "🌙 Dark",
                                horizontal=True,
                                key="settings_theme_radio")
        if theme_choice != st.session_state.theme:
            st.session_state.theme = theme_choice
            api_put("/auth/theme", json={"theme": theme_choice})
            st.success(f"Theme set to {theme_choice}")
            time.sleep(0.5)
            st.rerun()

        st.markdown("---")
        st.markdown("### 🌍 Language")
        lang_choice = st.radio("Choose language",
                               ["en", "hi"],
                               index=0 if st.session_state.language == "en" else 1,
                               format_func=lambda x: "English" if x == "en" else "हिन्दी",
                               horizontal=True,
                               key="settings_lang_radio")
        if lang_choice != st.session_state.language:
            st.session_state.language = lang_choice
            api_put("/auth/language", json={"language": lang_choice})
            st.success("Language updated")
            time.sleep(0.5)
            st.rerun()

    with tab2:
        st.markdown("### 🔔 Notification Preferences")
        st.caption("Control which notifications you receive via email and in-app.")

        r = api_get("/notifications/preferences")
        prefs = handle_response(r, show_error=False) if r else None

        if not prefs:
            st.error("Cannot load preferences")
        else:
            with st.form("prefs_form"):
                st.markdown("**📧 Email Notifications**")
                email_on_grade = st.checkbox("Grade updates for linked students", value=prefs.get("email_on_grade", True))
                email_on_attendance = st.checkbox("Attendance alerts (absence/late)", value=prefs.get("email_on_attendance", True))
                email_on_fee = st.checkbox("Fee payment confirmations", value=prefs.get("email_on_fee", True))
                email_on_assignment = st.checkbox("New assignment alerts", value=prefs.get("email_on_assignment", True))
                email_on_report = st.checkbox("Weekly performance reports", value=prefs.get("email_on_report", False))

                st.markdown("**🔔 In-App Notifications**")
                inapp_on_all = st.checkbox("Show in-app notifications", value=prefs.get("inapp_on_all", True))

                if st.form_submit_button("💾 Save Preferences", type="primary", use_container_width=True):
                    payload = {
                        "email_on_grade": email_on_grade,
                        "email_on_attendance": email_on_attendance,
                        "email_on_fee": email_on_fee,
                        "email_on_assignment": email_on_assignment,
                        "email_on_report": email_on_report,
                        "inapp_on_all": inapp_on_all,
                    }
                    r = api_put("/notifications/preferences", json=payload)
                    if r and r.status_code == 200:
                        st.success("✅ Preferences saved!")
                        st.balloons()
                    else:
                        st.error("Failed to save")

    with tab3:
        st.markdown("### 🔑 Change Password")
        if st.button("Change Password", use_container_width=True):
            st.session_state.show_change_password = True
            st.rerun()

        st.markdown("---")
        st.markdown("### 🔐 Two-Factor Authentication")
        r = api_get("/auth/me")
        me = handle_response(r, show_error=False) if r else None
        twofa_on = me.get("twofa_enabled", False) if me else False

        if twofa_on:
            st.success("✅ 2FA is enabled on your account")
        else:
            st.warning("⚠️ 2FA is not enabled")
            st.markdown("""
            **Enable 2FA:**
            1. Install Google Authenticator (or Authy)
            2. Click Setup below
            3. Scan the QR code
            4. Enter the 6-digit code to confirm
            """)
            if st.button("🔒 Setup 2FA", type="primary"):
                r = api_post("/auth/2fa/setup")
                data = handle_response(r) if r else None
                if data:
                    st.session_state.fa_secret = data["secret"]
                    st.session_state.fa_qr = data["qr_code"]
                    st.rerun()

            if st.session_state.get("fa_qr"):
                c1, c2 = st.columns(2)
                with c1:
                    st.image(st.session_state.fa_qr, caption="Scan with authenticator app")
                with c2:
                    st.code(st.session_state.fa_secret, language="text")
                with st.form("verify_2fa_settings"):
                    code = st.text_input("Enter 6-digit code", max_chars=6)
                    if st.form_submit_button("✅ Verify & Enable", type="primary"):
                        r = api_post("/auth/2fa/verify", json={"code": code})
                        if r and r.status_code == 200:
                            st.success("✅ 2FA enabled!")
                            st.session_state.fa_qr = None
                            st.session_state.fa_secret = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(r.json().get("detail", "Invalid code"))


# ============================================================
# PAGE: USERS (ADMIN)
# ============================================================
elif selected == t("users") and user_role == "admin":
    st.markdown(f'<div class="main-header"><h1>{t("users")}</h1></div>', unsafe_allow_html=True)
    r = api_get("/auth/users")
    data = handle_response(r) if r else None
    if data:
        users = data["users"]
        st.metric("Total Users", len(users))
        st.dataframe(pd.DataFrame(users), use_container_width=True)

        st.markdown("### 🔧 Actions")
        opts = {f"{u['username']} ({u['role']})": u["id"] for u in users}
        sel = st.selectbox("Select user", list(opts.keys()), key="admin_sel")
        uid = opts[sel]
        selected_user = next((u for u in users if u["id"] == uid), None)
        current_role = selected_user["role"] if selected_user else "teacher"

        if uid == user["id"]:
            st.warning("⚠️ You selected your own account.")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 Toggle Active", use_container_width=True):
                r = api_put(f"/auth/users/{uid}/toggle")
                if r and r.status_code == 200:
                    st.success("Updated")
                    st.rerun()
        with c2:
            new_role = st.selectbox("New Role", ["admin", "teacher", "student", "parent"],
                                    index=["admin", "teacher", "student", "parent"].index(current_role),
                                    key="admin_role")
            if st.button("👤 Change Role", use_container_width=True):
                if new_role != current_role:
                    r = api_put(f"/auth/users/{uid}/role", json={"role": new_role})
                    if r and r.status_code == 200:
                        st.success(r.json().get("message", "Updated"))
                        st.rerun()
        with c3:
            if st.button("↩️ Revert Last", use_container_width=True, type="secondary"):
                r = api_put(f"/auth/users/{uid}/revert-role")
                if r and r.status_code == 200:
                    st.success(r.json().get("message", "Reverted"))
                    st.rerun()


        # ============================================================
        # CLASS ASSIGNMENTS (teacher access control)
        # ============================================================
        st.markdown("---")
        st.markdown("### 🏫 Class Assignments")
        st.caption("Assign which classes each teacher can access. Teachers only see students in their assigned classes.")

        # Fetch available classes
        _cls_resp = api_get("/auth/classes/all")
        _cls_data = handle_response(_cls_resp, show_error=False) if _cls_resp else None
        _all_classes = _cls_data.get("classes", []) if _cls_data else []

        if not _all_classes:
            st.info("No classes exist yet. Create students with a class first (e.g., CS-A) via the Analyze page.")
        else:
            # Filter to teacher users only
            _teachers = [u for u in users if u.get("role") == "teacher"]
            if not _teachers:
                st.info("No teacher accounts exist yet. Register a teacher first.")
            else:
                _t_opts = {f"{u['username']} ({u.get('full_name') or u['email']})": u["id"] for u in _teachers}
                _sel_teacher_label = st.selectbox(
                    "Select teacher",
                    options=list(_t_opts.keys()),
                    key="cls_teacher_select",
                )
                _sel_teacher_id = _t_opts[_sel_teacher_label]

                # Fetch current assignments
                _cur_resp = api_get(f"/auth/users/{_sel_teacher_id}/classes")
                _cur_data = handle_response(_cur_resp, show_error=False) if _cur_resp else None
                _current_classes = _cur_data.get("classes", []) if _cur_data else []

                st.caption(f"Currently assigned: {', '.join(_current_classes) if _current_classes else 'none'}")

                # Multi-select
                _chosen = st.multiselect(
                    "Classes to assign",
                    options=_all_classes,
                    default=_current_classes,
                    key="cls_multiselect",
                )

                _save_c1, _save_c2 = st.columns([1, 3])
                with _save_c1:
                    if st.button("💾 Save Assignments", type="primary", use_container_width=True):
                        _save_resp = api_post(
                            f"/auth/users/{_sel_teacher_id}/classes",
                            json={"class_names": _chosen},
                        )
                        if _save_resp and _save_resp.status_code == 200:
                            _result = _save_resp.json()
                            st.success(f"✅ {_result.get('message', 'Assigned')}")
                            st.balloons()
                            import time as _time; _time.sleep(0.5)
                            st.rerun()
                        else:
                            try:
                                _err = _save_resp.json().get("detail", "Failed")
                            except Exception:
                                _err = "Unknown error"
                            st.error(f"❌ {_err}")
                with _save_c2:
                    if _chosen != _current_classes:
                        st.caption(f"⚠️ Unsaved changes: {len(_chosen)} class(es) selected")
                    else:
                        st.caption("No pending changes")

                # Show all teacher assignments
                with st.expander("📋 View all teacher assignments"):
                    _all_rows = []
                    for _t in _teachers:
                        _r = api_get(f"/auth/users/{_t['id']}/classes")
                        _d = handle_response(_r, show_error=False) if _r else None
                        _cls = _d.get("classes", []) if _d else []
                        _all_rows.append({
                            "Teacher": _t["username"],
                            "Full Name": _t.get("full_name") or "—",
                            "Email": _t["email"],
                            "Assigned Classes": ", ".join(_cls) if _cls else "(none)",
                            "Count": len(_cls),
                        })
                    if _all_rows:
                        import pandas as _pd
                        st.dataframe(_pd.DataFrame(_all_rows), use_container_width=True, hide_index=True)


# ============================================================
# PAGE: AUDIT LOG (ADMIN)
# ============================================================
elif selected == t("audit") and user_role == "admin":
    st.markdown(f'<div class="main-header"><h1>{t("audit")}</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Activity", "🔐 Login Attempts"])
    with tab1:
        r = api_get("/audit/logs", params={"limit": 200})
        data = handle_response(r, show_error=False) if r else None
        if data and data.get("logs"):
            st.dataframe(pd.DataFrame(data["logs"]), use_container_width=True)
        else:
            st.info("No logs")
    with tab2:
        r = api_get("/audit/login-attempts", params={"limit": 200})
        data = handle_response(r, show_error=False) if r else None
        if data and data.get("attempts"):
            st.dataframe(pd.DataFrame(data["attempts"]), use_container_width=True)
        else:
            st.info("No attempts")


# ============================================================
# PARENT VIEW
# ============================================================
elif selected == t("my_children") and user_role == "parent":
    st.markdown(f'<div class="main-header"><h1>{t("my_children")}</h1></div>', unsafe_allow_html=True)
    r = api_get("/parents/my-children")
    data = handle_response(r, show_error=False) if r else None
    if data and data.get("children"):
        for c in data["children"]:
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 1rem;">
                <h3>🎓 {c['name']}</h3>
                <p><b>Grade:</b> {c['grade']} | <b>Average:</b> {c['average']:.2f}%</p>
                <p><b>Class:</b> {c.get('class_name', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No children linked yet. Contact admin.")


# ============================================================
# STUDENT VIEW
# ============================================================
elif selected == t("my_results") and user_role == "student":
    st.markdown(f'<div class="main-header"><h1>{t("my_results")}</h1></div>', unsafe_allow_html=True)
    r = api_get("/students", params={"limit": 10})
    data = handle_response(r, show_error=False) if r else None
    if data and data["count"] > 0:
        s = data["students"][0]
        st.markdown(f"### 🎓 {s['name']}")
        c1, c2, c3 = st.columns(3)
        with c1: render_metric("📊", f"{s['average']:.2f}%", "Average")
        with c2: render_metric("🏆", s["grade"], "Grade")
        with c3: render_metric("📈", f"{s['total_marks']:.0f}", "Total")


# ============================================================
# PAGE: TRENDS
# ============================================================
elif selected == t("trends") or selected == "📉 My Progress":
    st.markdown(f'<div class="main-header"><h1>{t("trends")}</h1></div>', unsafe_allow_html=True)
    r = api_get("/students", params={"limit": 100})
    data = handle_response(r, show_error=False) if r else None
    if data and data["count"] > 0:
        opts = {f"{s['name']}": s["id"] for s in data["students"]}
        sel = st.selectbox("Student", list(opts.keys()))
        if st.button("📊 Analyze", type="primary"):
            r = api_get(f"/trends/{opts[sel]}")
            res = handle_response(r, show_error=False) if r else None
            if res:
                if "Not enough" in res.get("message", ""):
                    st.warning(res["message"])
                elif "error" in res:
                    st.error(res["error"])
                else:
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("First", f"{res['first_average']:.2f}")
                    with c2: st.metric("Current", f"{res['current_average']:.2f}")
                    with c3: st.metric("Change", f"{res['improvement']:+.2f}")


# ============================================================
# PAGE: IMPORT/EXPORT
# ============================================================
elif selected == t("import_export"):
    st.markdown(f'<div class="main-header"><h1>{t("import_export")}</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📥 Import", "📤 Export"])
    with tab1:
        st.info("For advanced bulk import with preview, use the **📥 Bulk Import** page in the sidebar.")
    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊 CSV", use_container_width=True, key="e1"):
                r = api_get("/export/csv")
                if r and r.status_code == 200:
                    st.download_button("💾 Save CSV", data=r.content,
                                       file_name="students.csv", mime="text/csv")
        with c2:
            if st.button("📋 JSON", use_container_width=True, key="e2"):
                r = api_get("/export/json")
                if r and r.status_code == 200:
                    st.download_button("💾 Save JSON", data=json.dumps(r.json(), indent=2),
                                       file_name="students.json", mime="application/json")
        with c3:
            if st.button("📈 Excel", use_container_width=True, key="e3"):
                r = api_get("/export/excel")
                if r and r.status_code == 200:
                    st.download_button("💾 Save .xlsx", data=r.content,
                                       file_name="students.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")




# ============================================================
# PAGE: CLASS ASSIGNMENTS (admin only)
# ============================================================
elif selected == "🏫 Class Assignments" and user_role == "admin":
    st.markdown(
        '<div class="main-header"><h1>🏫 Class Assignments</h1>'
        '<p>Control which classes each teacher can access</p></div>',
        unsafe_allow_html=True,
    )

    r = api_get("/auth/users")
    data = handle_response(r, show_error=False) if r else None
    users_list = data.get("users", []) if data else []

    _cls_resp = api_get("/auth/classes/all")
    _cls_data = handle_response(_cls_resp, show_error=False) if _cls_resp else None
    _all_classes = _cls_data.get("classes", []) if _cls_data else []

    teachers = [u for u in users_list if u.get("role") == "teacher"]

    if not users_list:
        st.error("Cannot load users. Please refresh.")
    elif not teachers:
        st.info("No teacher accounts exist yet. Register a teacher first (Register tab).")
    elif not _all_classes:
        st.warning("No classes exist yet. Create a student with a class name (e.g., CS-A) via the Analyze page.")
    else:
        c1, c2 = st.columns([3, 2])

        with c1:
            st.markdown("### 🎯 Assign Classes to a Teacher")

            _t_opts = {
                f"{u['username']} ({u.get('full_name') or u['email']})": u["id"]
                for u in teachers
            }
            _sel_label = st.selectbox(
                "Select a teacher",
                options=list(_t_opts.keys()),
                key="cls_page_teacher",
            )
            _sel_id = _t_opts[_sel_label]

            _cur_resp = api_get(f"/auth/users/{_sel_id}/classes")
            _cur_data = handle_response(_cur_resp, show_error=False) if _cur_resp else None
            _current = _cur_data.get("classes", []) if _cur_data else []

            st.markdown("**Available classes:**")
            _chosen = st.multiselect(
                "Classes",
                options=_all_classes,
                default=_current,
                key="cls_page_multiselect",
                label_visibility="collapsed",
            )

            _c1, _c2, _c3 = st.columns([2, 1, 2])
            with _c1:
                if st.button("💾 Save Assignments", type="primary", use_container_width=True):
                    _save = api_post(
                        f"/auth/users/{_sel_id}/classes",
                        json={"class_names": _chosen},
                    )
                    if _save and _save.status_code == 200:
                        st.success("Assignments saved.")
                        st.balloons()
                        import time as _t; _t.sleep(0.6)
                        st.rerun()
                    else:
                        try:
                            _err = _save.json().get("detail", "Failed")
                        except Exception:
                            _err = "Unknown error"
                        st.error(f"Failed: {_err}")
            with _c2:
                if st.button("🔄 Reset", use_container_width=True):
                    st.rerun()
            with _c3:
                if _chosen != _current:
                    st.caption("Unsaved changes")
                else:
                    st.caption("Synced")

        with c2:
            st.markdown("### 📋 All Teacher Assignments")

            _all_rows = []
            for _t in teachers:
                _r = api_get(f"/auth/users/{_t['id']}/classes")
                _d = handle_response(_r, show_error=False) if _r else None
                _cls = _d.get("classes", []) if _d else []
                _all_rows.append({
                    "Teacher": _t["username"],
                    "Full Name": _t.get("full_name") or "—",
                    "Assigned": ", ".join(_cls) if _cls else "(none)",
                    "Count": len(_cls),
                })

            if _all_rows:
                import pandas as _pd
                st.dataframe(
                    _pd.DataFrame(_all_rows),
                    use_container_width=True,
                    hide_index=True,
                )

        st.markdown("---")
        st.info(
            "Teachers see only students in their assigned classes. "
            "A teacher with no assignments sees zero students. "
            "Changes take effect on the teacher's next page load."
        )




# ============================================================
# PAGE: GRADE SCHEMES (admin only)
# ============================================================
elif selected == "⚙️ Grade Schemes" and user_role == "admin":
    st.markdown(
        '<div class="main-header"><h1>⚙️ Grade Schemes</h1>'
        '<p>Define custom grading boundaries for your school</p></div>',
        unsafe_allow_html=True,
    )

    _gs_resp = api_get("/grade-schemes")
    _gs_data = handle_response(_gs_resp, show_error=False) if _gs_resp else None
    _schemes = _gs_data.get("schemes", []) if _gs_data else []

    # ---------- List schemes ----------
    st.markdown("### 📋 All Schemes")
    if not _schemes:
        st.info("No schemes yet. Create one below.")
    else:
        for _s in _schemes:
            _is_default = bool(_s.get("is_default"))
            _border = "#10b981" if _is_default else "#e2e8f0"
            _badge = ("<span style='background:#10b98122;color:#10b981;padding:0.15rem 0.5rem;"
                      "border-radius:6px;font-size:0.7rem;font-weight:600;'>✓ DEFAULT</span>"
                      if _is_default else "")

            st.markdown(
                f"""
                <div style="border:1px solid {_border};border-radius:10px;
                            padding:0.75rem 1rem;margin-bottom:0.5rem;
                            background:{'rgba(16,185,129,0.05)' if _is_default else 'transparent'};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <b style="font-size:1.05rem;">{_s.get('name','')}</b> {_badge}
                            <div style="color:#6b7280;font-size:0.85rem;margin-top:0.2rem;">
                                {_s.get('description','') or '(no description)'}
                            </div>
                        </div>
                        <div style="color:#9ca3af;font-size:0.8rem;">
                            {len(_s.get('boundaries', []))} tiers
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Boundaries table for this scheme
            with st.expander(f"View boundaries — {_s.get('name')}"):
                if _s.get("boundaries"):
                    import pandas as _pd
                    _bd = _pd.DataFrame(_s["boundaries"])
                    st.dataframe(_bd, use_container_width=True, hide_index=True)

            # Actions
            _ac1, _ac2, _ac3, _sp = st.columns([1, 1, 1, 5])
            with _ac1:
                if not _is_default:
                    if st.button("⭐ Set default", key=f"set_def_{_s['id']}"):
                        _r = api_put(f"/grade-schemes/{_s['id']}", json={"is_default": True})
                        if _r and _r.status_code == 200:
                            st.success("Set as default")
                            st.rerun()
                        else:
                            st.error("Failed to set default")
            with _ac2:
                if not _is_default:
                    if st.button("🗑️ Delete", key=f"del_{_s['id']}"):
                        _r = api_delete(f"/grade-schemes/{_s['id']}")
                        if _r and _r.status_code == 200:
                            st.success("Deleted")
                            st.rerun()
                        else:
                            try:
                                _e = _r.json().get("detail", "Failed")
                            except Exception:
                                _e = "Failed"
                            st.error(_e)

    st.markdown("---")

    # ---------- Create new scheme ----------
    st.markdown("### ➕ Create New Scheme")
    with st.expander("Create a scheme", expanded=False):
        _new_name = st.text_input("Scheme name", placeholder="e.g., CBSE Indian", key="gs_new_name")
        _new_desc = st.text_input("Description (optional)", key="gs_new_desc")
        _new_default = st.checkbox("Set as default", key="gs_new_default")

        st.markdown("**Grade boundaries** (define each tier):")
        st.caption("Example: A+ from 91 to 100, points 10. Scores between 91-100 get A+.")

        # Simple editor: up to 8 tiers
        _tiers = []
        _default_tiers = [
            ("A+", 90, 100, 10),
            ("A",  80, 89,  9),
            ("B",  70, 79,  8),
            ("C",  60, 69,  7),
            ("D",  50, 59,  6),
            ("E",  40, 49,  5),
            ("F",  0,  39,  0),
        ]

        for _i, (_dg, _dmin, _dmax, _dpts) in enumerate(_default_tiers):
            _c1, _c2, _c3, _c4 = st.columns([2, 2, 2, 2])
            with _c1:
                _g = st.text_input(f"Grade {_i+1}", value=_dg, key=f"gs_g_{_i}")
            with _c2:
                _mn = st.number_input(f"Min {_i+1}", value=float(_dmin), min_value=0.0, max_value=100.0, step=1.0, key=f"gs_mn_{_i}")
            with _c3:
                _mx = st.number_input(f"Max {_i+1}", value=float(_dmax), min_value=0.0, max_value=100.0, step=1.0, key=f"gs_mx_{_i}")
            with _c4:
                _pt = st.number_input(f"Points {_i+1}", value=int(_dpts), min_value=0, max_value=10, step=1, key=f"gs_pt_{_i}")
            _tiers.append({"grade": _g, "min": _mn, "max": _mx, "points": _pt})

        if st.button("💾 Create Scheme", type="primary", key="gs_create"):
            if not _new_name.strip():
                st.error("Scheme name is required")
            else:
                _payload = {
                    "name": _new_name.strip(),
                    "description": _new_desc.strip() or None,
                    "boundaries": _tiers,
                    "is_default": _new_default,
                }
                _r = api_post("/grade-schemes/create", json=_payload)
                if _r and _r.status_code == 200:
                    st.success("Scheme created!")
                    st.balloons()
                    st.rerun()
                else:
                    try:
                        _e = _r.json().get("detail", "Failed")
                    except Exception:
                        _e = "Unknown error"
                    st.error(f"Failed: {_e}")

    st.markdown("---")

    # ---------- Preview ----------
    st.markdown("### 🔮 Preview")
    st.caption("See what grade a score would get under each scheme.")

    if _schemes:
        _pv_score = st.number_input("Test score", min_value=0.0, max_value=100.0, value=75.0, step=1.0, key="gs_preview_score")

        _preview_rows = []
        for _s in _schemes:
            _matched = None
            for _b in _s.get("boundaries", []):
                try:
                    if float(_b["min"]) <= _pv_score <= float(_b["max"]):
                        _matched = _b
                        break
                except Exception:
                    continue
            _preview_rows.append({
                "Scheme": _s.get("name"),
                "Grade": _matched["grade"] if _matched else "—",
                "Points": _matched["points"] if _matched else "—",
            })

        import pandas as _pd
        st.dataframe(_pd.DataFrame(_preview_rows), use_container_width=True, hide_index=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p>🎓 Student Marks Analyzer Pro v12.0.0 — Complete (Phases 1-4)</p>
    <p style="font-size: 0.8rem;">Logged in as {user_name} ({user_role})</p>
</div>
""", unsafe_allow_html=True)
