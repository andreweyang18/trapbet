"""Entry point: `streamlit run app/streamlit_app.py`. Pages live in app/pages/."""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="trapbet", page_icon="📊", layout="wide")

HERE = Path(__file__).resolve().parent
pages = [
    st.Page(str(HERE / "pages" / "results.py"), title="Results", default=True),
    st.Page(str(HERE / "pages" / "playground.py"), title="Playground"),
    st.Page(str(HERE / "pages" / "about.py"), title="About"),
]
st.navigation(pages).run()
