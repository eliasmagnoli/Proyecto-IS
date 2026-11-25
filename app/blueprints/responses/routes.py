from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.blueprints.users.auth import current_user, login_required
from app.extensions import db
from app.models.question import Question
from app.models.response import Response

bp = Blueprint("responses", __name__, url_prefix="/responses")


def _response_to_dict(response: Response) -> dict:
    return {
        "id": response.id,
        "body": response.body,
        "question_id": response.question_id,
        "author_id": response.author_id,
        "is_accepted": response.is_accepted,
        "published_at": response.published_at.isoformat(),
    }


@bp.post("/")
@login_required
def create_response():
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    question_id = data.get("question_id")

    if not body:
        return jsonify({"error": "El cuerpo de la respuesta es obligatorio."}), 400
    if not question_id:
        return jsonify({"error": "La pregunta es obligatoria."}), 400

    question = db.session.get(Question, question_id)
    if question is None:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    user = current_user()
    response = Response(
        body=body,
        question_id=question.id,
        author_id=user.id,
    )
    db.session.add(response)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo guardar la respuesta."}), 400

    return jsonify(_response_to_dict(response)), 201
