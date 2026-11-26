from app.extensions import db
from app.models import (
    AIAgent,
    Category,
    Question,
    Response,
    User,
)


def create_user(username, email):
    user = User(username=username, email=email)
    user.set_password("secreto123")
    db.session.add(user)
    db.session.commit()
    return user


def create_question(author):
    category = Category(name="Programación")
    question = Question(
        title="¿Qué es Python?",
        body="Quiero aprender.",
        author=author,
        category=category,
    )
    db.session.add(question)
    db.session.commit()
    return question


def login(client, email):
    return client.post(
        "/users/login",
        json={"email": email, "password": "secreto123"},
    )


def test_vote_requires_login(client):
    author = create_user("ana", "ana@example.com")
    question = create_question(author)

    response = client.post(
        f"/votes/{question.id}",
        json={"value": "upvote"},
    )

    assert response.status_code == 401


def test_user_can_upvote_question(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)
    login(client, voter.email)

    response = client.post(
        f"/votes/{question.id}",
        json={"value": "upvote"},
    )

    assert response.status_code == 201
    assert response.get_json()["value"] == "upvote"


def test_user_cannot_vote_own_question(client):
    author = create_user("ana", "ana@example.com")
    question = create_question(author)
    login(client, author.email)

    response = client.post(
        f"/votes/{question.id}",
        json={"value": "upvote"},
    )

    assert response.status_code == 403


def test_user_cannot_vote_twice(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)
    login(client, voter.email)

    client.post(f"/votes/{question.id}", json={"value": "upvote"})
    response = client.post(
        f"/votes/{question.id}",
        json={"value": "downvote"},
    )

    assert response.status_code == 409


def test_vote_with_invalid_value_fails(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)
    login(client, voter.email)

    response = client.post(
        f"/votes/{question.id}",
        json={"value": "neutral"},
    )

    assert response.status_code == 400


def test_vote_nonexistent_content_fails(client):
    voter = create_user("bob", "bob@example.com")
    login(client, voter.email)

    response = client.post(
        "/votes/9999",
        json={"value": "upvote"},
    )

    assert response.status_code == 404


def test_user_can_upvote_response(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)

    response_content = Response(
        body="Python es un lenguaje de programación.",
        author=author,
        question=question,
    )
    db.session.add(response_content)
    db.session.commit()
    login(client, voter.email)

    response = client.post(
        f"/votes/{response_content.id}",
        json={"value": "upvote"},
    )

    assert response.status_code == 201
    assert response.get_json()["value"] == "upvote"


def test_upvote_increases_human_author_reputation(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)
    login(client, voter.email)

    response = client.post(
        f"/votes/{question.id}",
        json={"value": "upvote"},
    )

    db.session.refresh(author)
    assert response.status_code == 201
    assert author.reputation == 1


def test_downvote_decreases_human_author_reputation(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)
    login(client, voter.email)

    response = client.post(
        f"/votes/{question.id}",
        json={"value": "downvote"},
    )

    db.session.refresh(author)
    assert response.status_code == 201
    assert author.reputation == -1


def test_duplicate_vote_does_not_change_reputation(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)
    login(client, voter.email)

    client.post(f"/votes/{question.id}", json={"value": "upvote"})
    response = client.post(
        f"/votes/{question.id}",
        json={"value": "downvote"},
    )

    db.session.refresh(author)
    assert response.status_code == 409
    assert author.reputation == 1


def test_ai_agent_can_receive_vote_without_human_reputation(client):
    voter = create_user("bob", "bob@example.com")

    agent = AIAgent(
        agent_name="Asistente",
        model_version="test-model",
    )
    db.session.add(agent)
    db.session.commit()

    question = create_question(voter)
    response_content = Response(
        body="Esta es una respuesta generada por IA.",
        author=agent,
        question=question,
    )
    db.session.add(response_content)
    db.session.commit()

    login(client, voter.email)

    response = client.post(
        f"/votes/{response_content.id}",
        json={"value": "upvote"},
    )

    assert response.status_code == 201
    assert not hasattr(agent, "reputation")
