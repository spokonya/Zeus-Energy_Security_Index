from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

trader_bp = Blueprint("trader", __name__)

VALID_COUNTRY_CODES = {
    "AT", "BE", "BG", "CZ", "DE", "ES", "FR", "HR", "HU", "LV", "NL", "PL", "PT", "RO", "SK",
}


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _serialize_row(row):
    item = dict(row)
    value = item.get("added_at")
    if isinstance(value, datetime):
        item["added_at"] = value.isoformat(sep=" ", timespec="seconds")
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


# zeus_api: get_trader_watchlist(user_id)
@trader_bp.route("/users/<int:user_id>/watchlist", methods=["GET"])
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
@trader_bp.route("/users/<int:user_id>/watchlist", methods=["PUT"])
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
