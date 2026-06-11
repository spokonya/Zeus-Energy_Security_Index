"""Save and browse frozen data snapshots on journalist visualization pages."""

import logging

import requests
import streamlit as st
from modules.journalist_notes import (
    CODE_TO_NAME,
    _format_context_header,
    _format_context_metrics,
)
from modules.zeus_api import create_snapshot, delete_snapshot, get_snapshots

logger = logging.getLogger(__name__)


def _country_label(country_code):
    if not country_code:
        return "—"
    return CODE_TO_NAME.get(country_code, country_code)


def _default_label(payload):
    header = _format_context_header(payload)
    return header or payload.get("page") or "Data snapshot"


def _load_snapshots(user_id, country_code=None):
    try:
        return get_snapshots(user_id, country_code=country_code)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not load snapshots: %s", exc)
        return None


def render_save_snapshot(
    user_id,
    *,
    country_code,
    payload,
    label=None,
    button_key,
):
    """One compact button to freeze the current on-screen data."""
    if not country_code or not payload:
        return

    label = (label or _default_label(payload))[:150]

    if st.button(
        "Save data snapshot",
        key=button_key,
        help="Store the metrics on screen for citation later. View saved snapshots under Journalist Notes.",
    ):
        try:
            create_snapshot(
                user_id,
                {
                    "country_code": country_code,
                    "label": label,
                    "payload": payload,
                },
            )
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not save snapshot: {exc}")
        else:
            st.toast("Snapshot saved")


def render_snapshots_library(user_id):
    """Saved snapshot list — shown as a tab on the Journalist Notes page."""
    snapshots = _load_snapshots(user_id)
    if snapshots is None:
        st.error("Could not load snapshots. Ensure the API is running.")
        return

    st.caption(
        "Frozen metric bundles from Country Snapshot, Comparison, and Gas Storage Risk. "
        "Use these when you need exact numbers for a story."
    )

    if not snapshots:
        st.info("No snapshots yet. Save one from a country or risk view while exploring data.")
        return

    noted_codes = sorted({s["country_code"] for s in snapshots if s.get("country_code")})
    filter_options = ["All snapshots", *noted_codes]
    filter_labels = {
        "All snapshots": "All snapshots",
        **{code: _country_label(code) for code in noted_codes},
    }
    selected_filter = st.selectbox(
        "Filter by country",
        filter_options,
        format_func=lambda value: filter_labels.get(value, value),
        key="snapshot_country_filter",
    )

    if selected_filter == "All snapshots":
        shown = snapshots
    else:
        shown = [s for s in snapshots if s.get("country_code") == selected_filter]

    st.caption(
        f"Showing {len(shown)} of {len(snapshots)} snapshot"
        f"{'s' if len(snapshots) != 1 else ''}"
    )

    for snapshot in shown:
        payload = snapshot.get("payload") or {}
        with st.container(border=True):
            head, del_col = st.columns([5, 1])
            with head:
                title = snapshot.get("label") or _default_label(payload)
                st.markdown(f"**{title}**")
                header = _format_context_header(payload)
                if header and header != title:
                    st.caption(header)
                metrics_line = _format_context_metrics(payload)
                if metrics_line:
                    st.caption(metrics_line)
                saved_at = snapshot.get("created_at") or ""
                if saved_at:
                    st.caption(f"Saved {saved_at}")
            with del_col:
                if st.button(
                    "Delete",
                    key=f"snap_del_{snapshot['snapshot_id']}",
                    use_container_width=True,
                ):
                    try:
                        delete_snapshot(user_id, snapshot["snapshot_id"])
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not delete snapshot: {exc}")
                    else:
                        st.rerun()
