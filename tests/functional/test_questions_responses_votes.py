import pytest

from app.extensions import db
from app.models import Category, Question, Response, Role, User
from app.patterns.strategy.provider import PROVIDERS


@pytest.fixture
def auth_client(app):
    user = User(
        username="gianella_test",
        email="gianella_test@example.com",
        role=Role.GENERAL_USER,
    )
    user.set_password("secreto123")
    other = User(
        username="otro_usuario",
        email="otro_usuario@example.com",
        role=Role.GENERAL_USER,
    )
    other.set_password("secreto123")
    category = Category(name="General")
    db.session.add_all([user, other, category])
    db.session.commit()

    logged_client = app.test_client()
    logged_client.post(
        "/users/login",
        json={"email": "gianella_test@example.com", "password": "secreto123"},
    )
    return logged_client, user, other, category


def test_questions_crud_and_validation(client, auth_client):
    logged_client, user, _, category = auth_client

    assert client.get("/questions/").status_code == 200
    assert client.get("/questions/").get_json() == []
    assert client.get("/questions/999").status_code == 404

    unauth = client.post(
        "/questions/",
        json={"title": "Titulo", "body": "Cuerpo", "category_id": category.id},
    )
    assert unauth.status_code == 401

    bad = logged_client.post("/questions/", json={"title": "", "body": ""})
    assert bad.status_code == 400

    res = logged_client.post(
        "/questions/",
        json={
            "title": "¿Cómo funciona SQLAlchemy?",
            "body": "Duda sobre relaciones y sesiones.",
            "category_id": category.id,
            "tags": ["Python", "flask", ""],
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "¿Cómo funciona SQLAlchemy?"
    assert data["author_id"] == user.id
    assert data["tags"] == ["python", "flask"]

    detail = client.get(f"/questions/{data['id']}")
    assert detail.status_code == 200
    assert detail.get_json()["id"] == data["id"]


def test_create_and_accept_response(app, client, auth_client):
    logged_client, user, _, category = auth_client

    question = Question(
        title="Pregunta de prueba",
        body="Contenido de prueba",
        author_id=user.id,
        category_id=category.id,
    )
    db.session.add(question)
    db.session.commit()

    assert (
        client.post(
            "/responses/",
            json={"body": "Respuesta anónima", "question_id": question.id},
        ).status_code
        == 401
    )

    assert logged_client.post("/responses/", json={"body": ""}).status_code == 400
    assert (
        logged_client.post(
            "/responses/",
            json={"body": "Respuesta huérfana", "question_id": 9999},
        ).status_code
        == 404
    )

    created = logged_client.post(
        "/responses/",
        json={"body": "Esta es la respuesta correcta.", "question_id": question.id},
    )
    assert created.status_code == 201
    resp_data = created.get_json()
    assert resp_data["is_accepted"] is False
    assert resp_data["author_id"] == user.id

    # Otro usuario no puede aceptar la respuesta de la pregunta de `user`
    other_client = app.test_client()
    other_client.post(
        "/users/login",
        json={"email": "otro_usuario@example.com", "password": "secreto123"},
    )
    forbidden = other_client.post(f"/responses/{resp_data['id']}/accept")
    assert forbidden.status_code == 403

    # El autor de la pregunta sí puede aceptarla
    accepted = logged_client.post(f"/responses/{resp_data['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.get_json()["is_accepted"] is True

    db.session.refresh(question)
    assert question.is_resolved is True
    saved_response = db.session.get(Response, resp_data["id"])
    assert saved_response.is_accepted is True


def test_vote_blueprint_and_votable_content_inheritance(client, auth_client):
    _, user, _, category = auth_client
    question = Question(
        title="Contenido votable",
        body="Cuerpo del contenido",
        author_id=user.id,
        category_id=category.id,
    )
    db.session.add(question)
    db.session.commit()

    assert question.id is not None
    assert question.type == "question"
    resp = client.get("/votes/")
    assert resp.status_code in (200, 404, 405)


def test_question_with_agent_tag_gets_an_ai_response(auth_client, monkeypatch):
    from app.models import AIAgent, Tag
    from app.patterns.strategy.fake_strategy import FakeStrategy

    monkeypatch.setitem(PROVIDERS, "gemini", lambda: FakeStrategy(response="Respuesta de la IA"))
    logged_client, _, _, category = auth_client
    agent = AIAgent(agent_name="helper", model_version="v1", trigger_tags=[Tag(name="ia-help")])
    db.session.add(agent)
    db.session.commit()

    response = logged_client.post(
        "/questions/",
        json={
            "title": "Ayuda",
            "body": "No entiendo",
            "category_id": category.id,
            "tags": ["ia-help"],
        },
    )

    assert response.status_code == 201
    answers = db.session.scalars(db.select(Response)).all()
    assert [(a.author.get_display_name(), a.body) for a in answers] == [
        ("helper", "Respuesta de la IA")
    ]
