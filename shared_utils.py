# =========================================================
# SHARED UTILITIES
# Common functions used across multiple pages/modules.
# =========================================================

import os
import re

import pandas as pd
import streamlit as st


# =========================================================
# PAGE ICON
# =========================================================

_DEFAULT_ICON = "\U0001f697"


def load_page_icon(base_dir=None):
    """Load the app icon from .streamlit/icon_b64.txt and return a data-URI string.

    Falls back to a car emoji when the file is missing or empty.
    """
    if base_dir is None:
        base_dir = os.path.dirname(__file__)
    icon_path = os.path.join(base_dir, ".streamlit", "icon_b64.txt")
    try:
        with open(icon_path, "r") as f:
            data = f.read().strip()
            if data:
                return f"data:image/png;base64,{data}"
    except Exception:
        pass
    return _DEFAULT_ICON


# =========================================================
# PWA META TAGS
# =========================================================

def inject_pwa_meta(page_icon):
    """Inject PWA-related <meta> and <link> tags into the page."""
    st.markdown(
        f'<meta name="application-name" content="Central Shaken">'
        f'<meta name="apple-mobile-web-app-title" content="Central Shaken">'
        f'<meta name="theme-color" content="#0d2a6e">'
        f'<link rel="shortcut icon" href="{page_icon}" type="image/png">',
        unsafe_allow_html=True,
    )


# =========================================================
# DARK-MODE CSS
# =========================================================

_DARK_MODE_CSS = """
<style>
.stApp {
    background-color: #1a1a2e !important;
}
[data-testid="stAppViewContainer"] {
    background-color: #1a1a2e !important;
}
[data-testid="stMain"] {
    background-color: #1a1a2e !important;
}
.stDataFrame {
    background-color: #16213e !important;
    color: #eaeaea !important;
}
.stDataFrame [data-testid="stDataFrame"] {
    background-color: #16213e !important;
}
.stDataFrame [data-testid="stDataFrame"] thead th {
    background-color: #0f3460 !important;
    color: #eaeaea !important;
    border-bottom: 2px solid #e94560 !important;
}
.stDataFrame [data-testid="stDataFrame"] tbody tr {
    background-color: #16213e !important;
    color: #eaeaea !important;
    border-bottom: 1px solid #0f3460 !important;
}
.stDataFrame [data-testid="stDataFrame"] tbody tr:hover {
    background-color: #1a1a2e !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #87ceeb !important;
    color: #1a1a2e !important;
}
.stButton > button {
    background-color: #1044b5 !important;
    color: #ffffff !important;
}
.stButton > button:hover {
    background-color: #0d2a6e !important;
}
.streamlit-expanderHeader {
    background-color: #0f3460 !important;
    color: #eaeaea !important;
}
h1, h2, h3, h4, h5, h6, p, span, div {
    color: #eaeaea !important;
}
[data-testid="stSidebar"] {
    background-color: #1044b5 !important;
}
[data-testid="stSidebar"] > div:first-child {
    background-color: #1044b5 !important;
}
</style>
"""


def inject_dark_mode_css():
    """Inject the dark-mode stylesheet into the current page."""
    st.markdown(_DARK_MODE_CSS, unsafe_allow_html=True)


# =========================================================
# PHONE / WHATSAPP HELPERS
# =========================================================

_PHONE_STRIP_RE = re.compile(r"[\s\-\(\)]")


def clean_phone_number(numero):
    """Strip spaces, hyphens and parentheses from a phone number string.

    Returns the cleaned digit string, or an empty string when the input is
    empty / NaN.
    """
    if not numero or (isinstance(numero, float) and pd.isna(numero)):
        return ""
    return _PHONE_STRIP_RE.sub("", str(numero))


def get_whatsapp_url(numero):
    """Return a ``https://wa.me/…`` URL for a Japanese phone number, or *None*."""
    clean = clean_phone_number(numero)
    if clean.startswith("0") and len(clean) >= 10:
        return f"https://wa.me/81{clean[1:]}"
    return None


def format_whatsapp_link(numero):
    """Return an HTML ``<a>`` link to WhatsApp, or the raw number as a string."""
    url = get_whatsapp_url(numero)
    if url:
        return f'<a href="{url}" target="_blank">{numero}</a>'
    if not numero or (isinstance(numero, float) and pd.isna(numero)):
        return ""
    return str(numero)


# =========================================================
# PAGE SETUP BOILERPLATE
# =========================================================

def setup_page(title, *, base_dir=None):
    """Run the common page-setup sequence shared by every Streamlit page.

    1. Load the page icon.
    2. Call ``st.set_page_config``.
    3. Inject the base CSS from ``ui_base``.
    4. Inject PWA meta tags.
    5. Require login.

    Returns the resolved *page_icon* string so callers can reuse it.
    """
    from ui_base import inject_base_css
    from auth import require_login

    page_icon = load_page_icon(base_dir)
    st.set_page_config(
        title,
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon=page_icon,
    )
    inject_base_css()
    inject_pwa_meta(page_icon)
    require_login()
    return page_icon
