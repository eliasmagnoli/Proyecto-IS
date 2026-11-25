from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.blueprints.users.auth import current_user, login_required
from app.extensions import db
from app.models.category import Category
from app.models.user import Role

bp = Blueprint("questions", __name__, url_prefix="/questions")


def category_to_dict(category: Category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
    }


def _is_admin() -> bool:
    user = current_user()
    return user is not None and user.role == Role.ADMIN


@bp.get("/categories")
def list_categories():
    categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
    return jsonify([category_to_dict(c) for c in categories]), 200


@bp.post("/categories")
@login_required
def create_category():
    if not _is_admin():
        return jsonify({"error": "Solo un administrador puede crear categorías."}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return jsonify({"error": "El nombre de la categoría es obligatorio."}), 400

    category = Category(name=name, description=description)
    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una categoría con ese nombre."}), 409

    return jsonify(category_to_dict(category)), 201


@bp.put("/categories/<int:category_id>")
@bp.patch("/categories/<int:category_id>")
@login_required
def update_category(category_id: int):
    if not _is_admin():
        return jsonify({"error": "Solo un administrador puede editar categorías."}), 403

    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Categoría no encontrada."}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return jsonify({"error": "El nombre de la categoría no puede estar vacío."}), 400
        category.name = new_name

    if "description" in data:
        category.description = (data.get("description") or "").strip()

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una categoría con ese nombre."}), 409

    return jsonify(category_to_dict(category)), 200