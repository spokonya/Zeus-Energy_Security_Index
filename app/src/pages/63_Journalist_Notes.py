import logging

logger = logging.getLogger(__name__)

import streamlit as st
from modules.journalist_notes import render_journalist_notes_library
from modules.journalist_snapshots import render_snapshots_library
from modules.nav import SideBarLinks, render_persona_page_nav

st.set_page_config(layout="wide")

SideBarLinks()

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("No user is logged in. Return to Home and log in as a journalist.")
    st.stop()

st.title("Journalist Notes")

tab_notes, tab_snapshots = st.tabs(["Notes", "Saved snapshots"])

with tab_notes:
    render_journalist_notes_library(user_id, show_title=False)

with tab_snapshots:
    render_snapshots_library(user_id)

st.divider()
render_persona_page_nav("pages/63_Journalist_Notes.py")
