"""Flask CLI commands."""
from __future__ import annotations

import click
from flask import Flask

from app.extensions import db


def register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Seed verified owner data and the initial administrator (idempotent)."""
        from app.services.seed import seed_database

        created = seed_database()
        click.echo("Seed complete: " + ", ".join(f"{k}={v}" for k, v in created.items()))

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--name", default="Administrator")
    @click.option("--role", default="admin", type=click.Choice(["admin", "editor", "viewer"]))
    def create_admin(email, password, name, role):
        """Create an administrator account."""
        from app.models.user import AdminUser

        normalized = email.strip().lower()
        if AdminUser.query.filter_by(email=normalized).first():
            raise click.ClickException("An account with that email already exists")
        user = AdminUser(name=name, email=normalized, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created {role} account: {normalized}")

    @app.cli.command("backup")
    @click.argument("action", default="create")
    def backup_command(action):
        """Create a JSON application backup. Usage: flask backup create"""
        from app.services.backup_service import create_backup, list_backups

        if action == "create":
            record = create_backup()
            click.echo(f"Backup created: {record['filename']} ({record['size_bytes']} bytes)")
        elif action == "list":
            for record in list_backups():
                click.echo(f"{record['filename']}  {record['size_bytes']} bytes")
        else:
            raise click.ClickException("Unknown action. Use create or list.")

    @app.cli.command("knowledge")
    @click.argument("action", default="rebuild")
    def knowledge_command(action):
        """Knowledge base operations. Usage: flask knowledge rebuild"""
        if action != "rebuild":
            raise click.ClickException("Supported action: rebuild")
        from app.ai.rag_service import rebuild_index

        result = rebuild_index()
        click.echo(
            f"Index rebuilt: {result['documents']} documents, {result['chunks']} chunks, "
            f"backend={result['backend']}"
        )

    @app.cli.command("purge-expired")
    def purge_expired():
        """Remove expired refresh tokens."""
        from app.models.base import utcnow
        from app.models.user import RefreshToken

        removed = RefreshToken.query.filter(RefreshToken.expires_at < utcnow()).delete()
        db.session.commit()
        click.echo(f"Removed {removed} expired refresh tokens")
