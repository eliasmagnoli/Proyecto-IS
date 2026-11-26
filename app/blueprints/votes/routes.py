from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.blueprints.users.auth import current_user, login_required
from app.extensions import db
from app.models import User, VotableContent, Vote, VoteType

bp = Blueprint("votes", __name__, url_prefix="/votes")


@bp.post("/<int:content_id>")
@login_required
def create_vote(content_id: int):
    user = current_user()
    data = request.get_json(silent=True) or {}

    value = data.get("value")
    try:
        vote_type = VoteType(value)
    except (ValueError, TypeError):
        return jsonify({"error": "Tipo de voto inválido."}), 400

    content = db.session.get(VotableContent, content_id)
    if content is None:
        return jsonify({"error": "Contenido no encontrado."}), 404

    if content.author.id == user.id:
        return jsonify({"error": "No podés votar tu propio contenido."}), 403

    vote = Vote(user=user, content=content, value=vote_type)
    db.session.add(vote)
    # La reputación solo corresponde a usuarios humanos, no a agentes de IA.
    if isinstance(content.author, User):
        if vote_type == VoteType.UPVOTE:
            content.author.reputation += 1
        else:
            content.author.reputation -= 1

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya votaste este contenido."}), 409

    return jsonify(
        {
            "id": vote.id,
            "content_id": content.id,
            "value": vote.value.value,
        }
    ), 201
