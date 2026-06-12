from flask import Flask
from dotenv import load_dotenv
import os
import logging

from backend.db_connection import init_app as init_db
from backend.routes.news_routes import news_bp
from backend.routes.user_routes import user_bp
from backend.routes.household_routes import household_bp
from backend.routes.saved_articles_routes import saved_articles_bp
from backend.routes.notes_routes import notes_bp
from backend.routes.snapshots_routes import snapshots_bp
from backend.routes.storage_routes import countries_storage_bp, storage_bp
from backend.routes.electricity_price_routes import electricity_price_bp
from backend.routes.trader_routes import trader_bp

def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('API startup')

    # Load environment variables from the .env file so they are
    # accessible via os.getenv() below.
    load_dotenv()

    # Secret key used by Flask for securely signing session cookies.
    # .strip() removes accidental leading/trailing whitespace from .env values.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY").strip()

    # Database connection settings — values come from the .env file.
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    # Register the routes from each Blueprint with the app object
    # and give a url prefix to each.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(news_bp, url_prefix="/news")
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(household_bp, url_prefix="/users")
    app.register_blueprint(saved_articles_bp, url_prefix="/users")
    app.register_blueprint(notes_bp, url_prefix="/users")
    app.register_blueprint(snapshots_bp, url_prefix="/users")
    app.register_blueprint(storage_bp, url_prefix="/stats/storage")
    app.register_blueprint(countries_storage_bp, url_prefix="/countries")
    app.register_blueprint(electricity_price_bp, url_prefix="/ml1")
    app.register_blueprint(trader_bp, url_prefix="/users")

    return app
