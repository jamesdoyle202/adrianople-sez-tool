from pathlib import Path

# App
APP_NAME = "Adrianople Group SEZ Tool"
PAGE_TITLE = APP_NAME
PAGE_LAYOUT = "centered"
PAGE_ICON = None

# Paths
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
POLYGONS_DIR = DATA_DIR / "polygons"
INDEX_FILE = DATA_DIR / "index.json"

# Colors
COLOR_BACKGROUND = "#f8f8f6"
COLOR_TEXT = "#1a1a1a"
COLOR_ACCENT = "#1a1a1a"
COLOR_BLUE = "#4a6274"
COLOR_BORDER = "#d4d4d0"
COLOR_SURFACE = "#ffffff"

# Typography
FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
FONT_SIZE_BASE = "16px"
FONT_SIZE_SMALL = "14px"
FONT_SIZE_HEADING = "28px"
FONT_WEIGHT_NORMAL = "400"
FONT_WEIGHT_MEDIUM = "500"
LINE_HEIGHT = "1.6"
LETTER_SPACING = "0.01em"

# Spacing
SPACING_SM = "0.5rem"
SPACING_MD = "1rem"
SPACING_LG = "2rem"
SPACING_XL = "4rem"

# UI
BUTTON_BORDER_RADIUS = "0"
BUTTON_PADDING = "0.75rem 2rem"
HIDE_STREAMLIT_CHROME = True

GLOBAL_CSS = f"""
<style>
    .stApp {{
        background-color: {COLOR_BACKGROUND};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_BASE};
        line-height: {LINE_HEIGHT};
        letter-spacing: {LETTER_SPACING};
    }}
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 {{
        color: {COLOR_TEXT};
    }}
    .stApp h1 {{
        font-size: {FONT_SIZE_HEADING};
        font-weight: {FONT_WEIGHT_NORMAL};
    }}
    .stApp a {{
        color: {COLOR_BLUE};
    }}
    .stButton > button {{
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_ACCENT};
        border-radius: {BUTTON_BORDER_RADIUS};
        padding: {BUTTON_PADDING};
        font-weight: {FONT_WEIGHT_NORMAL};
        font-family: {FONT_FAMILY};
    }}
    .stButton > button:hover {{
        background-color: {COLOR_ACCENT};
        color: {COLOR_SURFACE};
        border-color: {COLOR_ACCENT};
    }}
    .stButton > button:focus {{
        box-shadow: 0 0 0 1px {COLOR_BLUE};
    }}
    .stButton > button[kind="tertiary"] {{
        background-color: transparent;
        color: {COLOR_BLUE};
        border: none;
        padding: 0;
        font-size: {FONT_SIZE_SMALL};
    }}
    .stButton > button[kind="tertiary"]:hover {{
        background-color: transparent;
        color: {COLOR_TEXT};
        border: none;
        text-decoration: underline;
    }}
    .stButton > button[kind="tertiary"]:focus {{
        box-shadow: none;
    }}
    .db-entry {{
        padding: {SPACING_LG} 0;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    .db-entry:last-child {{
        border-bottom: none;
    }}
    .db-entry-title {{
        font-size: {FONT_SIZE_BASE};
        font-weight: {FONT_WEIGHT_MEDIUM};
        margin-bottom: {SPACING_SM};
    }}
    .db-entry-meta {{
        font-size: {FONT_SIZE_SMALL};
        color: {COLOR_TEXT};
        margin-bottom: {SPACING_SM};
    }}
    .db-entry-notes {{
        font-size: {FONT_SIZE_SMALL};
        color: {COLOR_BLUE};
        margin-bottom: {SPACING_MD};
    }}
    #MainMenu, footer, header {{
        visibility: {"hidden" if HIDE_STREAMLIT_CHROME else "visible"};
    }}
</style>
"""
