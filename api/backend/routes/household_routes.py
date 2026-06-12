from datetime import date, datetime

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

household_bp = Blueprint("household", __name__)

PROFILE_FIELDS = [
    "utility_provider",
    "monthly_bill_amount",
    "bill_due_date",
    "billing_frequency",
    "avg_monthly_kwh",
    "tariff_type",
    "notes",
]

REQUIRED_FIELDS = [f for f in PROFILE_FIELDS if f != "notes"]

VALID_BILLING_FREQUENCIES = ("Weekly", "Monthly", "Quarterly", "Annually")
VALID_TARIFF_TYPES = ("Fixed rate", "Variable rate", "Time-of-use")


def _serialize_profile(row):
    if not row:
        return row
    profile = dict(row)
    if isinstance(profile.get("bill_due_date"), (date, datetime)):
        profile["bill_due_date"] = profile["bill_due_date"].isoformat()
    if profile.get("monthly_bill_amount") is not None:
        profile["monthly_bill_amount"] = float(profile["monthly_bill_amount"])
    if profile.get("avg_monthly_kwh") is not None:
        profile["avg_monthly_kwh"] = float(profile["avg_monthly_kwh"])
    return profile


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _validate_profile_payload(data, require_all=True):
    if not data:
        return "Request body is required"

    fields = REQUIRED_FIELDS if require_all else [
        f for f in REQUIRED_FIELDS if f in data
    ]
    for field in fields:
        if field not in data or data[field] in (None, ""):
            return f"Missing required field: {field}"

    if "email" in data and "@" not in str(data["email"]):
        return "Invalid email address"

    if "billing_frequency" in data and data["billing_frequency"] not in VALID_BILLING_FREQUENCIES:
        return f"billing_frequency must be one of: {', '.join(VALID_BILLING_FREQUENCIES)}"

    if "tariff_type" in data and data["tariff_type"] not in VALID_TARIFF_TYPES:
        return f"tariff_type must be one of: {', '.join(VALID_TARIFF_TYPES)}"

    if "monthly_bill_amount" in data and float(data["monthly_bill_amount"]) <= 0:
        return "monthly_bill_amount must be greater than 0"

    if "avg_monthly_kwh" in data and float(data["avg_monthly_kwh"]) <= 0:
        return "avg_monthly_kwh must be greater than 0"

    return None


# zeus_api: get_household_profile(user_id)
@household_bp.route("/<int:user_id>/household-profile", methods=["GET"])
def get_household_profile(user_id):
    current_app.logger.info("GET /users/%s/household-profile", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                "SELECT * FROM household_profiles WHERE user_id = %s",
                (user_id,),
            )
            profile = cursor.fetchone()

        if not profile:
            return error_response("Household profile not found", 404)

        return jsonify(_serialize_profile(profile)), 200
    except Error as e:
        current_app.logger.error("Database error in get_household_profile: %s", e)
        return error_response(str(e))


# zeus_api: create_household_profile(user_id, profile)
@household_bp.route("/<int:user_id>/household-profile", methods=["POST"])
def create_household_profile(user_id):
    current_app.logger.info("POST /users/%s/household-profile", user_id)
    try:
        data = request.get_json()
        error = _validate_profile_payload(data, require_all=True)
        if error:
            return error_response(error, 400)

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                "SELECT profile_id FROM household_profiles WHERE user_id = %s",
                (user_id,),
            )
            if cursor.fetchone():
                return error_response("Household profile already exists for this user", 409)

            cursor.execute(
                """
                INSERT INTO household_profiles (
                    user_id, utility_provider,
                    monthly_bill_amount, bill_due_date, billing_frequency,
                    avg_monthly_kwh, tariff_type, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    data["utility_provider"].strip(),
                    data["monthly_bill_amount"],
                    data["bill_due_date"],
                    data["billing_frequency"],
                    data["avg_monthly_kwh"],
                    data["tariff_type"],
                    data.get("notes", "").strip() or None,
                ),
            )
            profile_id = cursor.lastrowid

        get_db().commit()
        current_app.logger.info("Created household profile id=%s for user_id=%s", profile_id, user_id)
        return jsonify({"message": "Household profile created", "profile_id": profile_id}), 201
    except Error as e:
        current_app.logger.error("Database error in create_household_profile: %s", e)
        return error_response(str(e))


# zeus_api: update_household_profile(user_id, profile)
@household_bp.route("/<int:user_id>/household-profile", methods=["PUT"])
def update_household_profile(user_id):
    current_app.logger.info("PUT /users/%s/household-profile", user_id)
    try:
        data = request.get_json()
        error = _validate_profile_payload(data, require_all=False)
        if error:
            return error_response(error, 400)

        update_fields = [f for f in PROFILE_FIELDS if f in data]
        if not update_fields:
            return error_response("No valid fields to update", 400)

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                "SELECT profile_id FROM household_profiles WHERE user_id = %s",
                (user_id,),
            )
            if not cursor.fetchone():
                return error_response("Household profile not found", 404)

            set_clause = ", ".join(f"{field} = %s" for field in update_fields)
            params = [data[field] for field in update_fields]
            params.append(user_id)
            cursor.execute(
                f"UPDATE household_profiles SET {set_clause} WHERE user_id = %s",
                params,
            )

        get_db().commit()
        return jsonify({"message": "Household profile updated successfully"}), 200
    except Error as e:
        current_app.logger.error("Database error in update_household_profile: %s", e)
        return error_response(str(e))


# zeus_api: delete_household_profile(user_id)
@household_bp.route("/<int:user_id>/household-profile", methods=["DELETE"])
def delete_household_profile(user_id):
    current_app.logger.info("DELETE /users/%s/household-profile", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                "SELECT profile_id FROM household_profiles WHERE user_id = %s",
                (user_id,),
            )
            if not cursor.fetchone():
                return error_response("Household profile not found", 404)

            cursor.execute(
                "DELETE FROM household_profiles WHERE user_id = %s",
                (user_id,),
            )

        get_db().commit()
        current_app.logger.info("Deleted household profile for user_id=%s", user_id)
        return jsonify({"message": "Household profile deleted successfully"}), 200
    except Error as e:
        current_app.logger.error("Database error in delete_household_profile: %s", e)
        return error_response(str(e))
