import click
from flask import Flask
from flask.cli import with_appcontext

from app.blueprints.users.services import RegistrationError, register_user
from app.extensions import db
from app.models import AIAgent, Role, Tag
from app.services.ai_agent_triggers import respond_to_unanswered_questions


@click.command("respond-unanswered")
@with_appcontext
def respond_unanswered_command():
    """Hace que los agentes de IA respondan las preguntas que nadie contestó a tiempo."""
    responses = respond_to_unanswered_questions()
    click.echo(f"Respuestas publicadas: {len(responses)}")


@click.command("create-agent")
@click.option("--name", required=True, help="Nombre visible del agente.")
@click.option("--model-version", default="v1", show_default=True)
@click.option("--timeout", "timeout_minutes", default=60, show_default=True, type=int)
@click.option("--tag", "tag_names", multiple=True, help="Etiqueta que activa al agente.")
@with_appcontext
def create_agent_command(name, model_version, timeout_minutes, tag_names):
    """Crea un agente de IA y lo asocia a las etiquetas indicadas."""
    tags = []
    for tag_name in tag_names:
        tag = db.session.scalar(db.select(Tag).filter_by(name=tag_name))
        tags.append(tag or Tag(name=tag_name))

    agent = AIAgent(
        agent_name=name,
        model_version=model_version,
        timeout_minutes=timeout_minutes,
        trigger_tags=tags,
    )
    db.session.add(agent)
    db.session.commit()
    click.echo(f"Agente creado: {agent.agent_name} (id {agent.id})")


@click.command("create-admin")
@click.option("--username", required=True)
@click.option("--email", required=True)
@click.password_option()
@with_appcontext
def create_admin_command(username, email, password):
    """Crea un usuario administrador."""
    try:
        user = register_user(username, email, password)
    except RegistrationError as error:
        for field, message in error.errors.items():
            click.echo(f"{field}: {message}", err=True)
        raise SystemExit(1) from None

    user.role = Role.ADMIN
    db.session.commit()
    click.echo(f"Administrador creado: {user.username}")


def register_commands(app: Flask) -> None:
    app.cli.add_command(respond_unanswered_command)
    app.cli.add_command(create_agent_command)
    app.cli.add_command(create_admin_command)
