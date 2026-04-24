"""Application factory."""
import logging
import os
from flask import Flask, redirect, url_for
from flask_login import current_user

from config import Config
from .extensions import db, login_manager, migrate, csrf


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faca login para acessar essa pagina."
    login_manager.login_message_category = "warning"

    from . import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    from .blueprints.auth import bp as auth_bp
    from .blueprints.candidates import bp as candidates_bp
    from .blueprints.funnel import bp as funnel_bp
    from .blueprints.reports import bp as reports_bp
    from .blueprints.sync import bp as sync_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.main import bp as main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(candidates_bp, url_prefix="/candidatos")
    app.register_blueprint(funnel_bp, url_prefix="/funil")
    app.register_blueprint(reports_bp, url_prefix="/relatorios")
    app.register_blueprint(sync_bp, url_prefix="/sync")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    from .cli import register_cli
    register_cli(app)

    if app.config.get("ENABLE_SCHEDULER") and os.getenv("WERKZEUG_RUN_MAIN") != "true":
        from .scheduler import init_scheduler
        try:
            init_scheduler(app)
        except Exception as exc:
            app.logger.warning("Scheduler nao iniciado: %s", exc)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("candidates.list_candidates"))
        return redirect(url_for("auth.login"))

    logging.basicConfig(level=logging.INFO)
    return app
