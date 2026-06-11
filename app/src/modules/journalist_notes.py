"""Reusable journalist notes UI for visualization pages."""

import logging

import requests
import streamlit as st
from modules.zeus_api import create_note, delete_note, get_notes, update_note

logger = logging.getLogger(__name__)

CODE_TO_NAME = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CZ": "Czech Republic", "DK": "Denmark", "FR": "France", "DE": "Germany",
    "HU": "Hungary", "IT": "Italy", "LV": "Latvia", "NL": "Netherlands",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia",
    "ES": "Spain",
}
ALL_COUNTRY_CODES = sorted(CODE_TO_NAME)

MAX_CONTENT_LEN = 2000


def _country_label(country_code):
    if not country_code:
        return "General"
    return CODE_TO_NAME.get(country_code, country_code)


def snapshot_note_context(country_name, country_code, summary):
    metrics = {
        "Storage level": f"{summary['latest_full']:.0f}%",
    }
    if summary.get("delta_30d") is not None:
        metrics["30-day change"] = f"{summary['delta_30d']:+.0f} pts"
    metrics["Stressed winters"] = (
        f"{summary['stressed_winters']} of {summary['total_winters']}"
    )
    if summary.get("worst_winter_min") is not None:
        metrics["Lowest winter on record"] = f"{summary['worst_winter_min']:.0f}%"

    return {
        "page": "Country Snapshot",
        "country": country_name,
        "country_code": country_code,
        "data_as_of": summary.get("latest_date"),
        "metrics": metrics,
    }


def comparison_note_context(a_name, b_name, a_row, b_row):
    winter = a_row.get("winter") or b_row.get("winter")
    return {
        "page": "Country Comparison",
        "countries": [a_name, b_name],
        "data_as_of": str(winter) if winter is not None else None,
        "metrics": {
            f"{a_name} risk": f"{float(a_row['risk_prob']):.0%}",
            f"{b_name} risk": f"{float(b_row['risk_prob']):.0%}",
            f"{a_name} storage entering winter": f"{float(a_row['storage_at_start']):.0f}%",
            f"{b_name} storage entering winter": f"{float(b_row['storage_at_start']):.0f}%",
            f"{a_name} October trend": f"{float(a_row['storage_trend_30d']):+.0f} pts",
            f"{b_name} October trend": f"{float(b_row['storage_trend_30d']):+.0f} pts",
            f"{a_name} verdict": str(a_row.get("verdict", "—")),
            f"{b_name} verdict": str(b_row.get("verdict", "—")),
        },
    }


def risk_note_context(
    country_name,
    country_code,
    *,
    risk_prob,
    at_risk,
    storage_at_start,
    storage_trend_30d,
    storage_volatility,
    winter,
):
    return {
        "page": "Gas Storage Risk",
        "country": country_name,
        "country_code": country_code,
        "data_as_of": str(winter) if winter is not None else None,
        "metrics": {
            "Risk probability": f"{float(risk_prob):.0%}",
            "Model verdict": "At risk" if at_risk else "Not at risk",
            "Storage entering winter": f"{float(storage_at_start):.0f}%",
            "October trend": f"{float(storage_trend_30d):+.0f} pts",
            "Volatility (90d)": f"{float(storage_volatility):.1f}",
        },
    }


def _format_context_header(context):
    if not context:
        return None

    parts = []
    country = context.get("country")
    countries = context.get("countries")
    if country:
        parts.append(country)
    elif countries:
        parts.append(" vs ".join(countries))

    page = context.get("page")
    if page:
        parts.append(page)

    data_as_of = context.get("data_as_of")
    if data_as_of:
        parts.append(f"data as of {data_as_of}")

    return " · ".join(parts) if parts else None


def _format_context_metrics(context):
    metrics = (context or {}).get("metrics") or {}
    if not metrics:
        return None
    return " · ".join(f"{label}: {value}" for label, value in metrics.items())


def _render_note_context(context, *, saved_at=None):
    header = _format_context_header(context)
    metrics_line = _format_context_metrics(context)

    if header:
        st.markdown(f"**{header}**")
    if metrics_line:
        st.caption(metrics_line)
    if saved_at:
        st.caption(f"Note saved {str(saved_at)[:10]}")


def _load_notes(user_id, country_code=None):
    try:
        return get_notes(user_id, country_code=country_code)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not load notes: %s", exc)
        return None


def render_journalist_notes(
    user_id,
    *,
    page_label,
    country_code=None,
    note_context=None,
):
    """
    Inline note panel for the current page context.
    Notes are scoped to country_code when provided; otherwise saved as general.
    """
    st.write("##### Journalist Notes")
    st.caption(
        f"Capture reactions to **{page_label}** so you can return to them later. "
        "Each note saves the country and data on screen when you write it. "
        "All notes also appear under **Journalist Notes** in the sidebar."
    )

    notes = _load_notes(user_id, country_code=country_code)
    if notes is None:
        st.warning("Could not load notes. Ensure the API is running.")
        return

    with st.expander("Add a note", expanded=not notes):
        if note_context:
            with st.container(border=True):
                st.caption("This context will be saved with your note:")
                _render_note_context(note_context)

        with st.form(f"add_note_{page_label}_{country_code or 'general'}"):
            content = st.text_area(
                "Your observation",
                placeholder="What stands out in the data? Story angles, questions for sources...",
                max_chars=MAX_CONTENT_LEN,
            )
            if st.form_submit_button("Save note", type="primary"):
                if not content.strip():
                    st.error("Write something before saving.")
                else:
                    payload = {
                        "content": content.strip(),
                        "country_code": country_code,
                    }
                    if note_context:
                        payload["context"] = note_context
                    try:
                        create_note(user_id, payload)
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not save note: {exc}")
                    else:
                        st.rerun()

    if not notes:
        st.info("No notes for this view yet. Add one above while the chart is fresh.")
        return

    st.caption(f"{len(notes)} note{'s' if len(notes) != 1 else ''} for this view")

    for note in notes:
        with st.container(border=True):
            meta_col, action_col = st.columns([4, 1])
            with meta_col:
                saved_at = note.get("created_at") or note.get("updated_at") or ""
                _render_note_context(note.get("context"), saved_at=saved_at)
                st.markdown(note["content"])
            with action_col:
                if st.button(
                    "Delete",
                    key=f"del_{page_label}_{note['note_id']}",
                    use_container_width=True,
                ):
                    try:
                        delete_note(user_id, note["note_id"])
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not delete note: {exc}")
                    else:
                        st.rerun()

            with st.expander("Edit"):
                with st.form(f"edit_{page_label}_{note['note_id']}"):
                    edited = st.text_area(
                        "Edit note",
                        value=note["content"],
                        max_chars=MAX_CONTENT_LEN,
                    )
                    if st.form_submit_button("Save changes", type="primary"):
                        if not edited.strip():
                            st.error("Note cannot be empty.")
                        else:
                            try:
                                update_note(
                                    user_id,
                                    note["note_id"],
                                    {"content": edited.strip()},
                                )
                            except requests.exceptions.RequestException as exc:
                                st.error(f"Could not update note: {exc}")
                            else:
                                st.rerun()


def render_journalist_notes_library(user_id, *, show_title=True):
    """Full notes library with country filter — used on the Journalist Notes page."""
    if show_title:
        st.title("Journalist Notes")
    st.write(
        "#### Stored notes across country snapshots, comparisons, and risk views"
    )

    all_notes = _load_notes(user_id)
    if all_notes is None:
        st.error("Could not load notes. Ensure the API is running.")
        return

    noted_codes = sorted({n["country_code"] for n in all_notes if n.get("country_code")})
    filter_options = ["All notes", "General (no country)", *noted_codes]
    filter_labels = {
        "All notes": "All notes",
        "General (no country)": "General (no country)",
        **{code: _country_label(code) for code in noted_codes},
    }

    selected_filter = st.selectbox(
        "Filter by country",
        filter_options,
        format_func=lambda value: filter_labels.get(value, value),
    )

    if selected_filter == "All notes":
        shown = all_notes
    elif selected_filter == "General (no country)":
        shown = [n for n in all_notes if not n.get("country_code")]
    else:
        shown = [n for n in all_notes if n.get("country_code") == selected_filter]

    st.divider()

    with st.expander("Add a note"):
        with st.form("add_library_note"):
            tag = st.selectbox(
                "Tag (optional)",
                ["General", *[_country_label(c) for c in ALL_COUNTRY_CODES]],
                help="Link the note to a country, or leave as General.",
            )
            tag_code = None
            if tag != "General":
                tag_code = next(
                    (c for c in ALL_COUNTRY_CODES if _country_label(c) == tag),
                    None,
                )
            content = st.text_area(
                "Note",
                placeholder="Story lead, data caveat, follow-up question...",
                max_chars=MAX_CONTENT_LEN,
            )
            if st.form_submit_button("Save note", type="primary"):
                if not content.strip():
                    st.error("Write something before saving.")
                else:
                    library_context = {
                        "page": "Journalist Notes",
                        "country": tag if tag != "General" else None,
                        "metrics": {
                            "Tagged country": tag,
                        },
                    }
                    try:
                        create_note(
                            user_id,
                            {
                                "content": content.strip(),
                                "country_code": tag_code,
                                "context": library_context,
                            },
                        )
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not save note: {exc}")
                    else:
                        st.rerun()

    st.caption(
        f"Showing {len(shown)} of {len(all_notes)} note"
        f"{'s' if len(all_notes) != 1 else ''}"
    )

    if not shown:
        st.info("No notes match this filter.")
        return

    for note in shown:
        with st.container(border=True):
            head, del_col = st.columns([5, 1])
            with head:
                saved_at = note.get("created_at") or note.get("updated_at") or ""
                _render_note_context(note.get("context"), saved_at=saved_at)
                if not note.get("context"):
                    st.markdown(f"**{_country_label(note.get('country_code'))}**")
                st.write(note["content"])
            with del_col:
                if st.button(
                    "Delete",
                    key=f"lib_del_{note['note_id']}",
                    use_container_width=True,
                ):
                    try:
                        delete_note(user_id, note["note_id"])
                    except requests.exceptions.RequestException as exc:
                        st.error(f"Could not delete note: {exc}")
                    else:
                        st.rerun()

            with st.expander("Edit"):
                with st.form(f"lib_edit_{note['note_id']}"):
                    edited = st.text_area(
                        "Edit note",
                        value=note["content"],
                        max_chars=MAX_CONTENT_LEN,
                    )
                    if st.form_submit_button("Save changes", type="primary"):
                        if not edited.strip():
                            st.error("Note cannot be empty.")
                        else:
                            try:
                                update_note(
                                    user_id,
                                    note["note_id"],
                                    {"content": edited.strip()},
                                )
                            except requests.exceptions.RequestException as exc:
                                st.error(f"Could not update note: {exc}")
                            else:
                                st.rerun()
