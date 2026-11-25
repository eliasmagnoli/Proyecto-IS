from app.models import Question, Response, User
from app.patterns.factory.response_creator import ResponseCreator


class HumanResponseCreator(ResponseCreator):
    def __init__(self, user: User):
        self.user = user

    def _resolve_content(self, question: Question, raw_content: str | None) -> str:
        return (raw_content or "").strip()

    def _create_response(self, question: Question, content: str) -> Response:
        return Response(body=content, question=question, author=self.user)
