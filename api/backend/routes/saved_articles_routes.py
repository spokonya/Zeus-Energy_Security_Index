from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

saved_articles_bp = Blueprint("saved_articles", __name__)


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _serialize_row(row):
    article = dict(row)
    for field in ("pub_date", "saved_at"):
        value = article.get(field)
        if isinstance(value, datetime):
            article[field] = value.isoformat(sep=" ", timespec="seconds")
    return article


def _parse_pub_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace("T", " ")[:19]
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError:
        return None


# zeus_api: get_saved_articles(user_id)
@saved_articles_bp.route("/<int:user_id>/saved-articles", methods=["GET"])
def get_saved_articles(user_id):
    current_app.logger.info("GET /users/%s/saved-articles", user_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT article_id, user_id, title, link, source_name,
                       description, pub_date, saved_at
                FROM saved_articles
                WHERE user_id = %s
                ORDER BY saved_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in get_saved_articles: %s", e)
        return error_response(str(e))


# zeus_api: save_article(user_id, article)
@saved_articles_bp.route("/<int:user_id>/saved-articles", methods=["POST"])
def save_article(user_id):
    current_app.logger.info("POST /users/%s/saved-articles", user_id)
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", 400)

        title = (data.get("title") or "").strip()
        link = (data.get("link") or "").strip()
        if not title or not link:
            return error_response("Missing required fields: title, link", 400)

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT article_id FROM saved_articles
                WHERE user_id = %s AND link = %s
                """,
                (user_id, link),
            )
            if cursor.fetchone():
                return error_response("Article already saved", 409)

            cursor.execute(
                """
                INSERT INTO saved_articles (
                    user_id, title, link, source_name, description, pub_date
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    title,
                    link,
                    (data.get("source_name") or "").strip() or None,
                    (data.get("description") or "").strip() or None,
                    _parse_pub_date(data.get("pub_date")),
                ),
            )
            article_id = cursor.lastrowid

        get_db().commit()
        return jsonify({"message": "Article saved", "article_id": article_id}), 201
    except Error as e:
        current_app.logger.error("Database error in save_article: %s", e)
        return error_response(str(e))


# zeus_api: delete_saved_article(user_id, article_id)
@saved_articles_bp.route(
    "/<int:user_id>/saved-articles/<int:article_id>", methods=["DELETE"]
)
def delete_saved_article(user_id, article_id):
    current_app.logger.info(
        "DELETE /users/%s/saved-articles/%s", user_id, article_id
    )
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT article_id FROM saved_articles
                WHERE user_id = %s AND article_id = %s
                """,
                (user_id, article_id),
            )
            if not cursor.fetchone():
                return error_response("Saved article not found", 404)

            cursor.execute(
                "DELETE FROM saved_articles WHERE user_id = %s AND article_id = %s",
                (user_id, article_id),
            )

        get_db().commit()
        return jsonify({"message": "Article removed from favorites"}), 200
    except Error as e:
        current_app.logger.error("Database error in delete_saved_article: %s", e)
        return error_response(str(e))
