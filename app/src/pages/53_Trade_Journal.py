import logging
logger = logging.getLogger(__name__)

import datetime as dt

import pandas as pd
import streamlit as st
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.trader_data import BIDDING_ZONES, CODE_TO_NAME, ZONE_NAMES

st.set_page_config(layout="wide")

SideBarLinks()

trader = st.session_state.get("first_name", "Trader")

DIRECTIONS = ["Long", "Short", "Hedge"]
OUTCOMES = ["Pending", "Forecast correct", "Forecast wrong"]

st.title("Trade Journal")
st.write("#### Every decision you made against the forecast, and how it played out")
st.write(
    f"{trader}, log the call you made off each forecast, then come back and "
    "annotate how it resolved. Over time that's your personal read on how much "
    "to trust the model — by zone and by market regime."
)

# Notes live in session for this demo; a production build would persist them
# per user in the database. Seeded with a few examples so the page has history.
if "trader_notes" not in st.session_state:
    st.session_state["trader_notes"] = [
        {"id": 1, "date": dt.date(2026, 4, 20), "zone": "BE", "direction": "Long",
         "forecast_call": "Forecast +7% over 30 days",
         "note": "Went long on the projected climb into spring.",
         "outcome": "Forecast wrong",
         "outcome_note": "Prices stayed flat — scratched the trade."},
        {"id": 2, "date": dt.date(2026, 5, 12), "zone": "NL", "direction": "Short",
         "forecast_call": "Forecast -8%, high-wind week ahead",
         "note": "Faded the rally expecting wind to cap prices.",
         "outcome": "Forecast correct",
         "outcome_note": "Prices fell ~6%, covered for profit."},
        {"id": 3, "date": dt.date(2026, 5, 28), "zone": "DE", "direction": "Long",
         "forecast_call": "Forecast +11% over 30 days",
         "note": "Layered hedges on the steep upward price path.",
         "outcome": "Forecast correct",
         "outcome_note": "Spike materialised on a cold snap."},
        {"id": 4, "date": dt.date(2026, 6, 2), "zone": "FR", "direction": "Hedge",
         "forecast_call": "Range-bound forecast (+1%)",
         "note": "Rolled hedges on schedule, no directional bet.",
         "outcome": "Pending", "outcome_note": ""},
        {"id": 5, "date": dt.date(2026, 6, 5), "zone": "PL", "direction": "Long",
         "forecast_call": "Forecast +6% upward drift",
         "note": "Small long on the upward drift.",
         "outcome": "Pending", "outcome_note": ""},
    ]
    st.session_state["trader_next_note_id"] = 6

notes = st.session_state["trader_notes"]

# ---- Track record summary ---------------------------------------------------
annotated = [n for n in notes if n["outcome"] != "Pending"]
correct = sum(1 for n in annotated if n["outcome"] == "Forecast correct")
hit_rate = (correct / len(annotated) * 100) if annotated else None

st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Trades logged",
    len(notes),
    help="Total trade notes you have saved against forecasts in this session.",
)
c2.metric(
    "Annotated",
    len(annotated),
    help="Trades where you recorded whether the forecast call was correct or wrong.",
)
c3.metric(
    "Awaiting outcome",
    len(notes) - len(annotated),
    help="Trades still marked Pending — not yet annotated with a result.",
)
c4.metric(
    "Forecast hit rate",
    f"{hit_rate:.0f}%" if hit_rate is not None else "—",
    f"{correct}/{len(annotated)} correct" if annotated else None,
    delta_color="off",
    help="Share of annotated trades where the forecast direction matched what actually happened.",
)

# ---- Log a new trade note ---------------------------------------------------
st.divider()
with st.expander("Log a trade note"):
    with st.form("new_note", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        n_date = f1.date_input("Trade date", value=dt.date.today())
        n_zone = f2.selectbox("Bidding zone", ZONE_NAMES,
                              index=ZONE_NAMES.index("Netherlands"))
        n_dir = f3.selectbox("Position", DIRECTIONS)
        n_call = st.text_input(
            "Forecast you acted on",
            placeholder="e.g. Forecast +9% over 30 days",
        )
        n_note = st.text_area(
            "Rationale", placeholder="Why you put the trade on against the data.")
        if st.form_submit_button("Save note", type="primary"):
            st.session_state["trader_notes"].append({
                "id": st.session_state["trader_next_note_id"],
                "date": n_date, "zone": BIDDING_ZONES[n_zone], "direction": n_dir,
                "forecast_call": n_call, "note": n_note,
                "outcome": "Pending", "outcome_note": "",
            })
            st.session_state["trader_next_note_id"] += 1
            st.rerun()

# ---- Filters (story 5) ------------------------------------------------------
st.divider()
st.write("##### History")

logged_codes = sorted({n["zone"] for n in notes})
fcol1, fcol2 = st.columns([2, 2])
zone_filter = fcol1.multiselect(
    "Filter by bidding zone",
    [CODE_TO_NAME[c] for c in logged_codes],
    help="Leave empty to show every zone.",
)
all_dates = [n["date"] for n in notes]
date_range = fcol2.date_input(
    "Date range",
    value=(min(all_dates), max(all_dates)) if all_dates else dt.date.today(),
)

filter_codes = {BIDDING_ZONES[n] for n in zone_filter} if zone_filter else None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min(all_dates), max(all_dates)

shown = [
    n for n in notes
    if (filter_codes is None or n["zone"] in filter_codes)
    and start_date <= n["date"] <= end_date
]
shown = sorted(shown, key=lambda n: n["date"], reverse=True)

st.caption(f"Showing {len(shown)} of {len(notes)} notes.")

# ---- Notes list + outcome annotation (story 4) ------------------------------
# (text color, background color) for the status pill on each note.
OUTCOME_PILL = {
    "Forecast correct": ("#1B7F4B", "#E6F4EC"),
    "Forecast wrong":   ("#B42318", "#FCE9E7"),
    "Pending":          ("#5A6472", "#EEF0F3"),
}


def status_pill(outcome: str) -> str:
    fg, bg = OUTCOME_PILL[outcome]
    return (
        f"<span style='display:inline-block;background:{bg};color:{fg};"
        "padding:0.15rem 0.7rem;border-radius:999px;font-size:0.72rem;"
        f"font-weight:700;letter-spacing:0.03em;text-transform:uppercase;'>"
        f"{outcome}</span>"
    )


for n in shown:
    zone_name = CODE_TO_NAME.get(n["zone"], n["zone"])
    with st.container(border=True):
        head, badge = st.columns([3, 1])
        head.markdown(
            f"**{n['date']} · {zone_name} · {n['direction']}**  \n"
            f"<span style='color:#5A6472'>Forecast acted on:</span> "
            f"{n['forecast_call'] or '—'}",
            unsafe_allow_html=True,
        )
        badge.markdown(
            f"<div style='text-align:right'>{status_pill(n['outcome'])}</div>",
            unsafe_allow_html=True,
        )

        if n["note"]:
            st.write(n["note"])

        if n["outcome"] != "Pending" and n["outcome_note"]:
            st.caption(f"Outcome: {n['outcome']} — {n['outcome_note']}")

        with st.expander("Annotate outcome"):
            with st.form(f"annotate_{n['id']}"):
                outcome = st.radio(
                    "How did the forecast call play out?",
                    OUTCOMES,
                    index=OUTCOMES.index(n["outcome"]),
                    horizontal=True,
                )
                outcome_note = st.text_input(
                    "Outcome note", value=n["outcome_note"],
                    placeholder="What actually happened to price / your P&L.",
                )
                if st.form_submit_button("Save outcome", type="primary"):
                    n["outcome"] = outcome
                    n["outcome_note"] = outcome_note
                    st.rerun()

if not shown:
    st.info("No trade notes match these filters.")

st.divider()
render_persona_page_nav("pages/53_Trade_Journal.py")
