from app.extensions import db
from app.models import Category, Question, Response, User, Vote, VoteType


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


def create_response(author, question):
    response = Response(
        body="Python es un lenguaje de programación.",
        author=author,
        question=question,
    )
    db.session.add(response)
    db.session.commit()
    return response


def test_list_questions_includes_score(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)

    db.session.add_all(
        [
            Vote(user=voter, content=question, value=VoteType.UPVOTE),
        ]
    )
    db.session.commit()

    response = client.get("/questions/")

    assert response.status_code == 200
    assert response.get_json()[0]["score"] == 1


def test_get_question_includes_score(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    question = create_question(author)

    db.session.add_all(
        [
            Vote(user=voter, content=question, value=VoteType.DOWNVOTE),
        ]
    )
    db.session.commit()

    response = client.get(f"/questions/{question.id}")

    assert response.status_code == 200
    assert response.get_json()["score"] == -1


def test_get_nonexistent_question_returns_404(client):
    response = client.get("/questions/9999")

    assert response.status_code == 404


def test_list_responses_includes_score(client):
    author = create_user("ana", "ana@example.com")
    voter = create_user("bob", "bob@example.com")
    second_voter = create_user("carla", "carla@example.com")
    third_voter = create_user("diego", "diego@example.com")

    question = create_question(author)
    answer = create_response(author, question)

    votes = [
        Vote(user=voter, content=answer, value=VoteType.UPVOTE),
        Vote(user=second_voter, content=answer, value=VoteType.UPVOTE),
        Vote(user=third_voter, content=answer, value=VoteType.DOWNVOTE),
    ]
    db.session.add_all(votes)
    db.session.commit()

    response = client.get(f"/responses/question/{question.id}")

    assert response.status_code == 200
    assert response.get_json()[0]["score"] == 1


def test_list_responses_for_nonexistent_question_returns_404(client):
    response = client.get("/responses/question/9999")

    assert response.status_code == 404
