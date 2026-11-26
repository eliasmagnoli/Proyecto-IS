from datetime import UTC, datetime, timedelta

from app.cli import create_admin_command, create_agent_command, respond_unanswered_command
from app.extensions import db
from app.models import AIAgent, Category, Question, Response, Role, User
from app.patterns.strategy.fake_strategy import FakeStrategy


def test_create_agent_creates_the_agent_with_its_tags(app):
    runner = app.test_cli_runner()

    result = runner.invoke(
        create_agent_command, ["--name", "helper", "--tag", "ia-help", "--tag", "flask"]
    )

    assert result.exit_code == 0
    agent = db.session.scalar(db.select(AIAgent))
    assert agent.agent_name == "helper"
    assert {tag.name for tag in agent.trigger_tags} == {"ia-help", "flask"}


def test_create_admin_creates_a_user_with_the_admin_role(app):
    runner = app.test_cli_runner()

    result = runner.invoke(
        create_admin_command,
        ["--username", "root", "--email", "root@example.com"],
        input="secreto123\nsecreto123\n",
    )

    assert result.exit_code == 0
    user = db.session.scalar(db.select(User).filter_by(username="root"))
    assert user.role == Role.ADMIN
    assert user.check_password("secreto123")


def test_create_admin_reports_validation_errors(app):
    runner = app.test_cli_runner()

    result = runner.invoke(
        create_admin_command,
        ["--username", "r", "--email", "malo"],
        input="123\n123\n",
    )

    assert result.exit_code == 1
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0


def test_respond_unanswered_command_runs_the_process(app, monkeypatch):
    monkeypatch.setattr("app.services.ai_agent_triggers.strategy_from_env", lambda: FakeStrategy())
    user = User(username="ana", email="ana@example.com")
    user.set_password("secreto123")
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
    db.session.add_all(
        [
            AIAgent(agent_name="helper", model_version="v1", timeout_minutes=60),
            Question(
                title="Vieja",
                body="x",
                author=user,
                category=Category(name="Flask"),
                published_at=old,
            ),
        ]
    )
    db.session.commit()

    result = app.test_cli_runner().invoke(respond_unanswered_command)

    assert result.exit_code == 0
    assert "Respuestas publicadas: 1" in result.output
    assert db.session.scalar(db.select(db.func.count()).select_from(Response)) == 1
