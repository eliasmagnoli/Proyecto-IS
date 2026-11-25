import logging
from collections.abc import Callable

from app.extensions import db
from app.models import AIAgent, Question, Response, Tag
from app.patterns.factory.ai_response_creator import AIResponseCreator
from app.patterns.strategy.llm_strategy import LLMStrategy
from app.patterns.strategy.provider import strategy_from_env

logger = logging.getLogger(__name__)


def agents_for_question(question: Question) -> list[AIAgent]:
    """Agentes que se activan con alguna de las etiquetas de la pregunta."""
    tag_ids = [tag.id for tag in question.tags]
    if not tag_ids:
        return []

    query = db.select(AIAgent).join(AIAgent.trigger_tags).where(Tag.id.in_(tag_ids)).distinct()
    return list(db.session.scalars(query))


def has_responded(agent: AIAgent, question: Question) -> bool:
    query = db.select(Response.id).filter_by(question_id=question.id, author_id=agent.id)
    return db.session.scalar(query) is not None


def trigger_agents(
    question: Question,
    strategy_factory: Callable[[], LLMStrategy] = strategy_from_env,
) -> list[Response]:
    """Hace que los agentes asociados a las etiquetas de la pregunta la respondan.

    Pensada para llamarse justo después de guardar la pregunta. Nunca lanza
    excepciones: si el LLM falla, la pregunta queda publicada y el error se registra.
    """
    responses = []

    for agent in agents_for_question(question):
        if has_responded(agent, question):
            continue

        try:
            agent.set_strategy(strategy_factory())
            responses.append(AIResponseCreator(agent).publish_response(question))
        except Exception:
            db.session.rollback()
            logger.exception(
                "El agente %r no pudo responder la pregunta %s.", agent.agent_name, question.id
            )

    return responses
