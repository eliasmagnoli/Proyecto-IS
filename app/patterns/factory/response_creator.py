from abc import ABC, abstractmethod

from app.extensions import db
from app.models import Question, Response


class ResponseCreator(ABC):
    """Creador del patrón Factory Method: define el flujo único de publicación."""

    def publish_response(self, question: Question, raw_content: str | None = None) -> Response:
        content = self._resolve_content(question, raw_content)
        if not content.strip():
            raise ValueError("El contenido de la respuesta no puede estar vacío.")

        response = self._create_response(question, content)
        db.session.add(response)
        db.session.commit()
        return response

    @abstractmethod
    def _resolve_content(self, question: Question, raw_content: str | None) -> str:
        """Paso 1: consigue el texto de la respuesta."""

    @abstractmethod
    def _create_response(self, question: Question, content: str) -> Response:
        """Método fábrica, paso 2: construye la Response con el autor correspondiente."""
