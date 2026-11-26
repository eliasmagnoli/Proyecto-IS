from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Question, Response

bp = Blueprint("responses", __name__, url_prefix="/responses")


def _response_to_dict(response: Response) -> dict:
    return {
        "id": response.id,
        "body": response.body,
        "score": response.calculate_score(),
        "author_id": response.author_id,
        "question_id": response.question_id,
        "created_at": response.published_at.isoformat(),
    }


@bp.get("/question/<int:question_id>")
def list_question_responses(question_id: int):
    question = db.session.get(Question, question_id)

    if question is None:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    responses = db.session.scalars(
        db.select(Response)
        .where(Response.question_id == question_id)
        .order_by(Response.published_at.asc(), Response.id.asc())
    ).all()

    return jsonify([_response_to_dict(response) for response in responses]), 200
