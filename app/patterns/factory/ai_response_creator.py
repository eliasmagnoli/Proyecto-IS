from app.models import AIAgent, Question, Response
from app.patterns.factory.response_creator import ResponseCreator


class AIResponseCreator(ResponseCreator):
    def __init__(self, agent: AIAgent):
        self.agent = agent

    def _resolve_content(self, question: Question, raw_content: str | None) -> str:
        # El texto lo genera el agente con su estrategia; raw_content se ignora.
        return self.agent.generate_auto_response(question)

    def _create_response(self, question: Question, content: str) -> Response:
        return Response(body=content, question=question, author=self.agent)
