from datetime import datetime
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


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _serialize_row(row):
    item = dict(row)
    for field in ("added_at", "created_at", "updated_at"):
        value = item.get(field)
        if isinstance(value, datetime):
            item[field] = value.isoformat(sep=" ", timespec="seconds")
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


# zeus_api: get_trader_price_alerts(user_id)
@trader_bp.route("/users/<int:user_id>/price-alerts", methods=["GET"])
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
    "/users/<int:user_id>/price-alerts/<country_code>", methods=["PUT"]
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
    "/users/<int:user_id>/price-alerts/<country_code>", methods=["DELETE"]
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
