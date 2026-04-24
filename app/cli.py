"""Comandos CLI do Flask (flask seed, flask sync-converts)."""
import click
from flask import current_app
from flask.cli import with_appcontext

from .extensions import db
from .models import User


def register_cli(app):
    @app.cli.command("seed")
    @with_appcontext
    def seed_command():
        """Cria o usuario admin inicial e tabelas se necessario."""
        db.create_all()
        email = current_app.config["ADMIN_EMAIL"]
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(f"Usuario admin {email} ja existe (id={existing.id}).")
            return
        admin = User(
            name=current_app.config["ADMIN_NAME"],
            email=email,
            role="admin",
            active=True,
        )
        admin.set_password(current_app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin criado: {email}")

    @app.cli.command("sync-converts")
    @with_appcontext
    def sync_converts_cmd():
        """Executa a sincronizacao com Converts manualmente via CLI."""
        from .converts.sync_service import run_sync
        log = run_sync(triggered_by="cli")
        click.echo(f"Sync finalizado. status={log.status} novos={log.inserted} duplicados={log.duplicates}")

    @app.cli.command("create-user")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    @click.option("--name", required=True)
    @click.option("--role", default="operacional", type=click.Choice(["admin", "operacional"]))
    @with_appcontext
    def create_user_cmd(email, password, name, role):
        if User.query.filter_by(email=email).first():
            click.echo("Usuario ja existe.")
            return
        u = User(name=name, email=email, role=role, active=True)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        click.echo(f"Usuario {email} criado como {role}.")
