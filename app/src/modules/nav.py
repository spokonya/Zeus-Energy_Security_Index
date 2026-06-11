# Sidebar navigation and lightweight RBAC for Zeus personas.

import streamlit as st

from modules.theme import apply_zeus_theme


def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


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


PERSONA_ROUTES = {
    "household_owner": [
        ("pages/40_Household_Owner_Dashboard.py", "Dashboard"),
        ("pages/41_Household_Persona_Info.py", "My Info"),
        ("pages/42_Household_Energy_News.py", "Energy News"),
    ],
    "journalist": [
        ("pages/60_Country_Snapshot.py", "Country Snapshot"),
        ("pages/61_Country_Comparison.py", "Country Comparison"),
        ("pages/62_Gas_Storage_Risk.py", "Gas Storage Risk"),
        ("pages/63_Journalist_Notes.py", "Journalist Notes"),
    ],
    "energy_trader": [
        ("pages/51_Price_Forecast.py", "30-Day Price Forecast"),
        ("pages/52_My_Markets.py", "My Markets"),
        ("pages/53_Trade_Journal.py", "Trade Journal"),
    ],
}


def render_persona_page_nav(current_page: str) -> None:
    """Bottom-of-page prev/next nav following each persona's sidebar order."""
    role = st.session_state.get("role")
    routes = PERSONA_ROUTES.get(role)
    if not routes:
        return

    paths = [path for path, _ in routes]
    try:
        index = paths.index(current_page)
    except ValueError:
        return

    prev_path, prev_label = routes[index - 1] if index > 0 else (None, None)
    next_path, next_label = routes[index + 1] if index < len(routes) - 1 else (None, None)
    landing_path, landing_label = routes[0]

    if index == 0:
        if next_path and st.button(
            f"{next_label} →",
            type="primary",
            use_container_width=True,
            key=f"persona_nav_fwd_{current_page}",
        ):
            st.switch_page(next_path)
        return

    nav_left, nav_right = st.columns(2)
    with nav_left:
        if prev_path and st.button(
            f"← {prev_label}",
            use_container_width=True,
            key=f"persona_nav_back_{current_page}",
        ):
            st.switch_page(prev_path)

    with nav_right:
        if index == len(routes) - 1:
            if st.button(
                f"{landing_label} →",
                type="primary",
                use_container_width=True,
                key=f"persona_nav_landing_{current_page}",
            ):
                st.switch_page(landing_path)
        elif next_path and st.button(
            f"{next_label} →",
            type="primary",
            use_container_width=True,
            key=f"persona_nav_fwd_{current_page}",
        ):
            st.switch_page(next_path)


def SideBarLinks(show_home=False):
    """Render sidebar links for the logged-in Zeus persona."""
    apply_zeus_theme()

    st.sidebar.image("assets/logo.png", width=150)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.get("authenticated") and not show_home:
        st.switch_page("Home.py")

    if show_home or st.session_state.get("authenticated"):
        home_nav()

    if st.session_state.get("authenticated"):
        role = st.session_state.get("role")
        if role == "household_owner":
            household_owner_nav()
        elif role == "journalist":
            journalist_nav()
        elif role == "energy_trader":
            energy_trader_nav()

    about_page_nav()

    if st.session_state.get("authenticated"):
        if st.sidebar.button("Logout"):
            st.session_state.pop("role", None)
            st.session_state.pop("user_id", None)
            st.session_state.pop("first_name", None)
            st.session_state["authenticated"] = False
            st.switch_page("Home.py")
