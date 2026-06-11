import logging

logger = logging.getLogger(__name__)

import streamlit as st
from modules.journalist_notes import render_journalist_notes_library
from modules.nav import SideBarLinks, render_persona_page_nav

st.set_page_config(layout="wide")

SideBarLinks()

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("No user is logged in. Return to Home and log in as a journalist.")
    st.stop()

render_journalist_notes_library(user_id)

st.divider()
render_persona_page_nav("pages/63_Journalist_Notes.py")
