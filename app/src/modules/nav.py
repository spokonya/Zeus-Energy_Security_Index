# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.

import streamlit as st

from modules.theme import apply_zeus_theme


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


# ---- Role: pol_strat_advisor ------------------------------------------------

def pol_strat_home_nav():
    st.sidebar.page_link(
        "pages/00_Pol_Strat_Home.py", label="Political Strategist Home", icon="👤"
    )


def world_bank_viz_nav():
    st.sidebar.page_link(
        "pages/01_World_Bank_Viz.py", label="World Bank Visualization", icon="🏦"
    )


def map_demo_nav():
    st.sidebar.page_link("pages/02_Map_Demo.py", label="Map Demonstration", icon="🗺️")


# ---- Role: usaid_worker -----------------------------------------------------

def usaid_worker_home_nav():
    st.sidebar.page_link(
        "pages/10_USAID_Worker_Home.py", label="USAID Worker Home", icon="🏠"
    )


def ngo_directory_nav():
    st.sidebar.page_link("pages/14_NGO_Directory.py", label="NGO Directory", icon="📁")


def add_ngo_nav():
    st.sidebar.page_link("pages/15_Add_NGO.py", label="Add New NGO", icon="➕")


def prediction_nav():
    st.sidebar.page_link(
        "pages/11_Prediction.py", label="Regression Prediction", icon="📈"
    )


def api_test_nav():
    st.sidebar.page_link("pages/12_API_Test.py", label="Test the API", icon="🛜")


def classification_nav():
    st.sidebar.page_link(
        "pages/13_Classification.py", label="Classification Demo", icon="🌺"
    )


# ---- Role: journalist -------------------------------------------------------

def journalist_nav():
    st.sidebar.markdown("**Journalist**")
    st.sidebar.page_link(
        "pages/60_Country_Snapshot.py",
        label="Country Snapshot",
        icon="🌍",
    )
    st.sidebar.page_link(
        "pages/61_Country_Comparison.py",
        label="Country Comparison",
        icon="⚖️",
    )
    st.sidebar.page_link(
        "pages/62_Gas_Storage_Risk.py",
        label="Gas Storage Risk",
        icon="⚠️",
    )
    st.sidebar.page_link(
        "pages/63_Journalist_Notes.py",
        label="Journalist Notes",
        icon="📓",
    )


# ---- Role: household_owner --------------------------------------------------

def household_owner_nav():
    st.sidebar.markdown("**Household owner**")
    st.sidebar.page_link(
        "pages/40_Household_Owner_Dashboard.py",
        label="Dashboard",
        icon="📊",
    )
    st.sidebar.page_link(
        "pages/41_Household_Persona_Info.py",
        label="My Info",
        icon="👤",
    )
    st.sidebar.page_link(
        "pages/42_Household_Energy_News.py",
        label="Energy News",
        icon="📰",
    )


# ---- Role: energy_trader ----------------------------------------------------

def energy_trader_nav():
    st.sidebar.markdown("**Energy Trader**")
    st.sidebar.page_link(
        "pages/51_Price_Forecast.py",
        label="30-Day Price Forecast",
        icon="📈",
    )
    st.sidebar.page_link(
        "pages/52_My_Markets.py",
        label="My Markets",
        icon="⭐",
    )
    st.sidebar.page_link(
        "pages/53_Trade_Journal.py",
        label="Trade Journal",
        icon="📓",
    )


# ---- Role: administrator ----------------------------------------------------

def admin_home_nav():
    st.sidebar.page_link("pages/20_Admin_Home.py", label="System Admin", icon="🖥️")


def ml_model_mgmt_nav():
    st.sidebar.page_link(
        "pages/21_ML_Model_Mgmt.py", label="ML Model Management", icon="🏢"
    )

def new_ml_model_nav():
    st.sidebar.page_link(
        "pages/22_Prettier_ML.py", label="New ML Model", icon="📈"
    )

# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    apply_zeus_theme()

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/logo.png", width=150)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # If no one is logged in, send them to the Home (login) page
    if not st.session_state.get("authenticated") and not show_home:
        st.switch_page("Home.py")

    if show_home or st.session_state.get("authenticated"):
        home_nav()

    if st.session_state.get("authenticated"):

        if st.session_state["role"] == "household_owner":
            household_owner_nav()

        if st.session_state["role"] == "journalist":
            journalist_nav()

        if st.session_state["role"] == "energy_trader":
            energy_trader_nav()

        if st.session_state["role"] == "pol_strat_advisor":
            pol_strat_home_nav()
            world_bank_viz_nav()
            map_demo_nav()

        if st.session_state["role"] == "usaid_worker":
            usaid_worker_home_nav()
            ngo_directory_nav()
            add_ngo_nav()
            prediction_nav()
            api_test_nav()
            classification_nav()

        if st.session_state["role"] == "administrator":
            admin_home_nav()
            ml_model_mgmt_nav()
            new_ml_model_nav()
            
    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            st.session_state.pop("role", None)
            st.session_state.pop("user_id", None)
            st.session_state.pop("first_name", None)
            st.session_state["authenticated"] = False
            st.switch_page("Home.py")
