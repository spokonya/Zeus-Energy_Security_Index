from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

trader_bp = Blueprint("trader", __name__)

VALID_COUNTRY_CODES = {
    "AT", "BE", "BG", "CZ", "DE", "ES", "FR", "HR", "HU", "LV", "NL", "PL", "PT", "RO", "SK",
}


VALID_DIRECTIONS = {"above", "below"}
VALID_TRADE_DIRECTIONS = {"Long", "Short", "Hedge"}
VALID_OUTCOMES = {"Pending", "Forecast correct", "Forecast wrong"}

MAX_FORECAST_CALL_LEN = 300
MAX_OUTCOME_NOTE_LEN = 500


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _serialize_row(row):
    item = dict(row)
    for field in ("added_at", "created_at", "updated_at"):
        value = item.get(field)
        if isinstance(value, datetime):
            item[field] = value.isoformat(sep=" ", timespec="seconds")
    trade_date = item.get("trade_date")
    if isinstance(trade_date, (date, datetime)):
        item["trade_date"] = trade_date.isoformat()
    threshold = item.get("threshold")
    if isinstance(threshold, Decimal):
        item["threshold"] = float(threshold)
    return item


def _normalize_country_code(value):
    if value is None:
        return None
    text = str(value).strip().upper()
    return text if text else None


def _normalize_country_codes(values):
    if not isinstance(values, list):
        return None
    codes = []
    seen = set()
    for value in values:
        code = _normalize_country_code(value)
        if not code:
            continue
        if code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return codes


def _validate_country_code(country_code):
    code = _normalize_country_code(country_code)
    if not code or code not in VALID_COUNTRY_CODES:
        return None
    return code


def _validate_direction(value):
    direction = (value or "").strip().lower()
    return direction if direction in VALID_DIRECTIONS else None


def _validate_trade_direction(value):
    direction = (value or "").strip()
    if direction == "long":
        direction = "Long"
    elif direction == "short":
        direction = "Short"
    elif direction == "hedge":
        direction = "Hedge"
    return direction if direction in VALID_TRADE_DIRECTIONS else None


def _validate_outcome(value):
    outcome = (value or "").strip()
    return outcome if outcome in VALID_OUTCOMES else None


def _parse_trade_date(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _optional_text(value, max_len=None):
    text = (value or "").strip()
    if not text:
        return None
    if max_len is not None and len(text) > max_len:
        return None
    return text


# zeus_api: get_trader_watchlist(user_id)
@trader_bp.route("/<int:user_id>/watchlist", methods=["GET"])
def get_trader_watchlist(user_id):
    current_app.logger.info("GET /users/%s/watchlist", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT watchlist_id, user_id, country_code, added_at
                FROM trader_watchlist
                WHERE user_id = %s
                ORDER BY added_at ASC, country_code ASC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in get_trader_watchlist: %s", e)
        return error_response(str(e))


# zeus_api: set_trader_watchlist(user_id, country_codes)
@trader_bp.route("/<int:user_id>/watchlist", methods=["PUT"])
def set_trader_watchlist(user_id):
    current_app.logger.info("PUT /users/%s/watchlist", user_id)
    try:
        data = request.get_json()
        if data is None:
            return error_response("Request body is required", 400)

        country_codes = _normalize_country_codes(data.get("country_codes"))
        if country_codes is None:
            return error_response("Missing required field: country_codes", 400)

        invalid = [code for code in country_codes if code not in VALID_COUNTRY_CODES]
        if invalid:
            return error_response(
                f"Invalid country code(s): {', '.join(invalid)}", 400
            )

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                "DELETE FROM trader_watchlist WHERE user_id = %s",
                (user_id,),
            )
            for code in country_codes:
                cursor.execute(
                    """
                    INSERT INTO trader_watchlist (user_id, country_code)
                    VALUES (%s, %s)
                    """,
                    (user_id, code),
                )

            cursor.execute(
                """
                SELECT watchlist_id, user_id, country_code, added_at
                FROM trader_watchlist
                WHERE user_id = %s
                ORDER BY added_at ASC, country_code ASC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        get_db().commit()
        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in set_trader_watchlist: %s", e)
        return error_response(str(e))


# zeus_api: get_trader_price_alerts(user_id)
@trader_bp.route("/<int:user_id>/price-alerts", methods=["GET"])
def get_trader_price_alerts(user_id):
    current_app.logger.info("GET /users/%s/price-alerts", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT alert_id, user_id, country_code, threshold, direction,
                       created_at, updated_at
                FROM trader_price_alerts
                WHERE user_id = %s
                ORDER BY country_code ASC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in get_trader_price_alerts: %s", e)
        return error_response(str(e))


# zeus_api: set_trader_price_alert(user_id, country_code, threshold, direction)
@trader_bp.route(
    "/<int:user_id>/price-alerts/<country_code>", methods=["PUT"]
)
def set_trader_price_alert(user_id, country_code):
    current_app.logger.info(
        "PUT /users/%s/price-alerts/%s", user_id, country_code
    )
    try:
        code = _validate_country_code(country_code)
        if not code:
            return error_response("Invalid country code", 400)

        data = request.get_json()
        if data is None:
            return error_response("Request body is required", 400)

        direction = _validate_direction(data.get("direction"))
        if not direction:
            return error_response(
                "Missing or invalid field: direction (above or below)", 400
            )

        threshold_raw = data.get("threshold")
        if threshold_raw is None:
            return error_response("Missing required field: threshold", 400)
        try:
            threshold = float(threshold_raw)
        except (TypeError, ValueError):
            return error_response("Invalid threshold value", 400)
        if threshold < 0:
            return error_response("Threshold must be non-negative", 400)

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                INSERT INTO trader_price_alerts (
                    user_id, country_code, threshold, direction
                ) VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    threshold = VALUES(threshold),
                    direction = VALUES(direction)
                """,
                (user_id, code, threshold, direction),
            )

            cursor.execute(
                """
                SELECT alert_id, user_id, country_code, threshold, direction,
                       created_at, updated_at
                FROM trader_price_alerts
                WHERE user_id = %s AND country_code = %s
                """,
                (user_id, code),
            )
            row = cursor.fetchone()

        get_db().commit()
        return jsonify(_serialize_row(row)), 200
    except Error as e:
        current_app.logger.error("Database error in set_trader_price_alert: %s", e)
        return error_response(str(e))


# zeus_api: delete_trader_price_alert(user_id, country_code)
@trader_bp.route(
    "/<int:user_id>/price-alerts/<country_code>", methods=["DELETE"]
)
def delete_trader_price_alert(user_id, country_code):
    current_app.logger.info(
        "DELETE /users/%s/price-alerts/%s", user_id, country_code
    )
    try:
        code = _validate_country_code(country_code)
        if not code:
            return error_response("Invalid country code", 400)

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT alert_id FROM trader_price_alerts
                WHERE user_id = %s AND country_code = %s
                """,
                (user_id, code),
            )
            if not cursor.fetchone():
                return error_response("Price alert not found", 404)

            cursor.execute(
                """
                DELETE FROM trader_price_alerts
                WHERE user_id = %s AND country_code = %s
                """,
                (user_id, code),
            )

        get_db().commit()
        return jsonify({"message": "Price alert cleared"}), 200
    except Error as e:
        current_app.logger.error(
            "Database error in delete_trader_price_alert: %s", e
        )
        return error_response(str(e))


# zeus_api: get_trader_trade_notes(user_id)
@trader_bp.route("/<int:user_id>/trade-notes", methods=["GET"])
def get_trader_trade_notes(user_id):
    current_app.logger.info("GET /users/%s/trade-notes", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT note_id, user_id, trade_date, country_code, direction,
                       forecast_call, note, outcome, outcome_note,
                       created_at, updated_at
                FROM trader_trade_notes
                WHERE user_id = %s
                ORDER BY trade_date DESC, note_id DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in get_trader_trade_notes: %s", e)
        return error_response(str(e))


# zeus_api: create_trader_trade_note(user_id, note)
@trader_bp.route("/<int:user_id>/trade-notes", methods=["POST"])
def create_trader_trade_note(user_id):
    current_app.logger.info("POST /users/%s/trade-notes", user_id)
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", 400)

        trade_date = _parse_trade_date(data.get("trade_date"))
        if not trade_date:
            return error_response("Missing or invalid field: trade_date", 400)

        country_code = _validate_country_code(data.get("country_code"))
        if not country_code:
            return error_response("Missing or invalid field: country_code", 400)

        direction = _validate_trade_direction(data.get("direction"))
        if not direction:
            return error_response(
                "Missing or invalid field: direction (Long, Short, or Hedge)", 400
            )

        forecast_call = _optional_text(
            data.get("forecast_call"), MAX_FORECAST_CALL_LEN
        )
        if data.get("forecast_call") and forecast_call is None:
            return error_response(
                f"forecast_call must be at most {MAX_FORECAST_CALL_LEN} characters",
                400,
            )

        note = _optional_text(data.get("note"))

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                INSERT INTO trader_trade_notes (
                    user_id, trade_date, country_code, direction,
                    forecast_call, note, outcome
                ) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
                """,
                (
                    user_id,
                    trade_date,
                    country_code,
                    direction,
                    forecast_call,
                    note,
                ),
            )
            note_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT note_id, user_id, trade_date, country_code, direction,
                       forecast_call, note, outcome, outcome_note,
                       created_at, updated_at
                FROM trader_trade_notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )
            row = cursor.fetchone()

        get_db().commit()
        return jsonify(_serialize_row(row)), 201
    except Error as e:
        current_app.logger.error("Database error in create_trader_trade_note: %s", e)
        return error_response(str(e))


# zeus_api: update_trader_trade_note(user_id, note_id, note)
@trader_bp.route("/<int:user_id>/trade-notes/<int:note_id>", methods=["PUT"])
def update_trader_trade_note(user_id, note_id):
    current_app.logger.info("PUT /users/%s/trade-notes/%s", user_id, note_id)
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", 400)

        outcome = _validate_outcome(data.get("outcome"))
        if not outcome:
            return error_response(
                "Missing or invalid field: outcome", 400
            )

        outcome_note = _optional_text(
            data.get("outcome_note"), MAX_OUTCOME_NOTE_LEN
        )
        if data.get("outcome_note") and outcome_note is None:
            return error_response(
                f"outcome_note must be at most {MAX_OUTCOME_NOTE_LEN} characters",
                400,
            )

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT note_id FROM trader_trade_notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )
            if not cursor.fetchone():
                return error_response("Trade note not found", 404)

            cursor.execute(
                """
                UPDATE trader_trade_notes
                SET outcome = %s, outcome_note = %s
                WHERE user_id = %s AND note_id = %s
                """,
                (outcome, outcome_note, user_id, note_id),
            )

            cursor.execute(
                """
                SELECT note_id, user_id, trade_date, country_code, direction,
                       forecast_call, note, outcome, outcome_note,
                       created_at, updated_at
                FROM trader_trade_notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )
            row = cursor.fetchone()

        get_db().commit()
        return jsonify(_serialize_row(row)), 200
    except Error as e:
        current_app.logger.error("Database error in update_trader_trade_note: %s", e)
        return error_response(str(e))


# zeus_api: delete_trader_trade_note(user_id, note_id)
@trader_bp.route("/<int:user_id>/trade-notes/<int:note_id>", methods=["DELETE"])
def delete_trader_trade_note(user_id, note_id):
    current_app.logger.info("DELETE /users/%s/trade-notes/%s", user_id, note_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT note_id FROM trader_trade_notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )
            if not cursor.fetchone():
                return error_response("Trade note not found", 404)

            cursor.execute(
                """
                DELETE FROM trader_trade_notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )

        get_db().commit()
        return jsonify({"message": "Trade note deleted"}), 200
    except Error as e:
        current_app.logger.error("Database error in delete_trader_trade_note: %s", e)
        return error_response(str(e))
