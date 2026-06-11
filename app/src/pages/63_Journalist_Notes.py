import logging

logger = logging.getLogger(__name__)

import streamlit as st
from modules.journalist_notes import render_journalist_notes_library
from modules.nav import SideBarLinks

st.set_page_config(layout="wide")

SideBarLinks()

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("No user is logged in. Return to Home and log in as a journalist.")
    st.stop()

render_journalist_notes_library(user_id)

st.divider()

nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("Country Snapshot", use_container_width=True):
        st.switch_page("pages/60_Country_Snapshot.py")
with nav_right:
    if st.button("Gas Storage Risk", use_container_width=True):
        st.switch_page("pages/62_Gas_Storage_Risk.py")
