from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.blueprints.users.auth import current_user, login_required
from app.extensions import db
from app.models.category import Category
from app.models.question import Question
from app.models.tag import Tag

bp = Blueprint("questions", __name__, url_prefix="/questions")


def _question_to_dict(question: Question) -> dict:
    return {
        "id": question.id,
        "title": question.title,
        "body": question.body,
        "author_id": question.author_id,
        "category_id": question.category_id,
        "tags": [tag.name for tag in question.tags],
        "created_at": question.created_at.isoformat(),
    }


@bp.post("/")
@login_required
def create_question():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    category_id = data.get("category_id")
    raw_tags = data.get("tags") or []

    if not title:
        return jsonify({"error": "El título es obligatorio."}), 400
    if not body:
        return jsonify({"error": "El cuerpo de la pregunta es obligatorio."}), 400
    if not category_id:
        return jsonify({"error": "La categoría es obligatoria."}), 400

    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Categoría no encontrada."}), 404

    user = current_user()
    tag_objects = []
    if isinstance(raw_tags, list):
        for raw_tag in raw_tags:
            tag_name = str(raw_tag).strip().lower()
            if not tag_name:
                continue
            existing_tag = db.session.scalar(db.select(Tag).where(Tag.name == tag_name))
            if existing_tag is None:
                existing_tag = Tag(name=tag_name)
                db.session.add(existing_tag)
            tag_objects.append(existing_tag)

    question = Question(
        title=title,
        body=body,
        author_id=user.id,
        category_id=category.id,
        tags=tag_objects,
    )
    db.session.add(question)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo guardar la pregunta."}), 400

    return jsonify(_question_to_dict(question)), 201