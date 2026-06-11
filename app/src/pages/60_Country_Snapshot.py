import logging
logger = logging.getLogger(__name__)

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from modules.journalist_notes import render_journalist_notes, snapshot_note_context
from modules.journalist_snapshots import render_save_snapshot
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.theme import zeus_plotly_layout
from modules.zeus_api import get_storage_history, get_storage_summary

st.set_page_config(layout='wide')

SideBarLinks()

st.title("Country Snapshot")
st.write("#### Ten years of gas storage by country")

NAME_TO_CODE = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR",
    "Czech Republic": "CZ", "Denmark": "DK", "France": "FR", "Germany": "DE",
    "Hungary": "HU", "Italy": "IT", "Latvia": "LV", "Netherlands": "NL",
    "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Slovakia": "SK",
    "Spain": "ES",
}
COUNTRIES = list(NAME_TO_CODE.keys())
STRESS_THRESHOLD = 30

default_country = st.session_state.get("journalist_country", "Poland")
selected_country = st.selectbox(
    "Select Country",
    COUNTRIES,
    index=COUNTRIES.index(default_country) if default_country in COUNTRIES else 0,
)
st.session_state["journalist_country"] = selected_country
code = NAME_TO_CODE[selected_country]

try:
    summary = get_storage_summary(code)
    history_payload = get_storage_history(code)
except requests.exceptions.HTTPError as exc:
    st.error(f"Could not load storage data from the API: {exc}")
    st.info("Ensure the API and database are running (`docker compose up -d`).")
    st.stop()
except requests.exceptions.RequestException as exc:
    st.error(f"Could not reach the API: {exc}")
    st.stop()

country_hist = pd.DataFrame(history_payload["history"])
country_hist["date"] = pd.to_datetime(country_hist["date"])

st.divider()

st.subheader(selected_country)

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Storage level",
    f"{summary['latest_full']:.0f}%",
    f"{summary['delta_30d']:+.0f} points past 30 days"
    if summary.get("delta_30d") is not None else None,
    help="Latest reported gas storage fill level as a percentage of total capacity.",
)
m2.metric(
    "Stressed winters",
    f"{summary['stressed_winters']} of {summary['total_winters']}",
    help="Number of winters on record when storage fell below the 30% stress threshold.",
)
m3.metric(
    "Lowest winter level on record",
    f"{summary['worst_winter_min']:.0f}%" if summary.get("worst_winter_min") is not None else "—",
    help="Minimum storage level reached during the worst winter in the historical data.",
)
m4.metric(
    "Stress threshold",
    f"{STRESS_THRESHOLD}%",
    help="Level EU analysts treat as critical — below 30%, withdrawal pressure and supply risk rise sharply.",
)
st.caption(
    f"Latest reported value: {summary['latest_date']}"
)

st.divider()

st.write(f"##### How {selected_country} fills and drains its storage")

fig = px.line(
    country_hist, x="date", y="full",
    labels={"date": "", "full": "Storage % full"},
)
fig.add_hline(
    y=STRESS_THRESHOLD, line_dash="dash", line_color="red",
    annotation_text="30% stress threshold",
)
zeus_plotly_layout(fig, height=400)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Typical fill cycle, fill through summer and drain "
    "through winter (Note how close the fill gets to the red line)"
)

st.divider()


stress_count = summary["stressed_winters"]
total_winters = summary["total_winters"]
worst = summary.get("worst_winter_min")
worst_winter = summary.get("worst_winter_year")

st.write("##### Recommendations")

current_level = summary["latest_full"]

if current_level < 40:
    st.warning(f"**Low: {current_level:.0f}% full**")
    st.markdown(
        "Storage this low before winter is a warning sign, and topping back up to the "
        "EU's 90% target by November 1 gets costly. Worth reporting on:\n\n"
        "&nbsp;&nbsp;1. Is the country buying LNG on the spot market to catch up, and at what price?\n\n"
        "&nbsp;&nbsp;2. Are neighboring countries sending gas through pipeline connections?\n\n"
        "&nbsp;&nbsp;3. Is the government discussing ways to cut demand this winter?"
    )
elif current_level < 70:
    st.info(f"**Mid-range: {current_level:.0f}% full**")
    st.markdown(
        "Storage is in a normal range, so the question is whether it is refilling fast "
        "enough to reach 90% by November 1. Worth watching:\n\n"
        "&nbsp;&nbsp;1. Is the level rising steadily, or has it stalled?\n\n"
        "&nbsp;&nbsp;2. Are high prices making it too expensive to refill right now?\n\n"
        "&nbsp;&nbsp;3. Is the country exporting gas instead of storing it?"
    )
else:
    st.success(f"**High: {current_level:.0f}% full**")
    st.markdown(
        "Storage is healthy and immediate risk is low, but kep watch:\n\n"
        "&nbsp;&nbsp;1. What did filling storage this high cost, and who paid for it?\n\n"
        "&nbsp;&nbsp;2. A full tank does not guarantee a safe winter. Our model shows storage can "
        "still fall below 30% if a cold snap hits, so the buffer matters as much as the starting level."
    )

st.divider()

user_id = st.session_state.get("user_id")
if user_id:
    snapshot_payload = snapshot_note_context(selected_country, code, summary)
    render_save_snapshot(
        user_id,
        country_code=code,
        payload=snapshot_payload,
        label=f"{selected_country} snapshot",
        button_key=f"snap_snapshot_{code}",
    )
    render_journalist_notes(
        user_id,
        page_label=f"{selected_country} snapshot",
        country_code=code,
        note_context=snapshot_payload,
    )
    st.divider()

render_persona_page_nav("pages/60_Country_Snapshot.py")
