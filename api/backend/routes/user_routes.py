from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.ml_countries import VALID_ML_COUNTRY_NAMES
from backend.utils import error_response
from mysql.connector import Error

VALID_PERSONAS = ("household_owner", "journalist", "energy_trader")
USER_FIELDS = ("display_name", "email", "country", "language")

user_bp = Blueprint("users", __name__)


# zeus_api: get_users()
@user_bp.route("", methods=["GET"])
def get_users():
    current_app.logger.info("GET /users")
    persona = request.args.get("persona")

    if not persona:
        return error_response("Missing required query parameter: persona", 400)
    if persona not in VALID_PERSONAS:
        return error_response(
            f"Invalid persona. Must be one of: {', '.join(VALID_PERSONAS)}",
            400,
        )

    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT user_id, display_name, persona, first_name, email, country, language
                FROM users
                WHERE persona = %s
                ORDER BY display_name
                """,
                (persona,),
            )
            users = cursor.fetchall()

        current_app.logger.info("Retrieved %s users for persona=%s", len(users), persona)
        return jsonify(users), 200
    except Error as e:
        current_app.logger.error("Database error in get_users: %s", e)
        return error_response(str(e))


# zeus_api: (called directly via requests in Home.py)
@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    current_app.logger.info("GET /users/%s", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT user_id, display_name, persona, first_name, email, country, language
                FROM users
                WHERE user_id = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()

        if not user:
            return error_response("User not found", 404)

        return jsonify(user), 200
    except Error as e:
        current_app.logger.error("Database error in get_user: %s", e)
        return error_response(str(e))


def _validate_user_payload(data, require_all=True):
    if not data:
        return "Request body is required"

    fields = USER_FIELDS if require_all else [f for f in USER_FIELDS if f in data]
    for field in fields:
        if field not in data or str(data[field]).strip() == "":
            return f"Missing required field: {field}"

    if "email" in data and "@" not in str(data["email"]):
        return "Invalid email address"

    if "country" in data and data["country"] not in VALID_ML_COUNTRY_NAMES:
        return (
            "country must be one of the supported forecast countries: "
            + ", ".join(VALID_ML_COUNTRY_NAMES)
        )

    return None


# zeus_api: update_user(user_id, payload)
@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    current_app.logger.info("PUT /users/%s", user_id)
    try:
        data = request.get_json()
        error = _validate_user_payload(data, require_all=False)
        if error:
            return error_response(error, 400)

        update_fields = [f for f in USER_FIELDS if f in data]
        if not update_fields:
            return error_response("No valid fields to update", 400)

        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT user_id, persona FROM users WHERE user_id = %s",
                (user_id,),
            )
            user = cursor.fetchone()
            if not user:
                return error_response("User not found", 404)

            if "country" in data and user["persona"] != "household_owner":
                return error_response(
                    "Country updates are only supported for household owners",
                    400,
                )

            set_clause = ", ".join(f"{field} = %s" for field in update_fields)
            params = [str(data[field]).strip() for field in update_fields]
            params.append(user_id)
            cursor.execute(
                f"UPDATE users SET {set_clause} WHERE user_id = %s",
                params,
            )

        get_db().commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Error as e:
        current_app.logger.error("Database error in update_user: %s", e)
        return error_response(str(e))
