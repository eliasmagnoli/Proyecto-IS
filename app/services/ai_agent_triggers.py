import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

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


def questions_waiting_for(agent: AIAgent, now: datetime) -> list[Question]:
    """Preguntas sin ninguna respuesta que ya esperaron más que el timeout del agente."""
    cutoff = now - timedelta(minutes=agent.timeout_minutes)
    has_answers = db.exists().where(Response.question_id == Question.id)

    query = (
        db.select(Question)
        .where(Question.published_at <= cutoff, ~has_answers)
        .order_by(Question.published_at)
    )
    return list(db.session.scalars(query))


def _publish_ai_response(
    agent: AIAgent,
    question: Question,
    strategy_factory: Callable[[], LLMStrategy],
) -> Response | None:
    try:
        agent.set_strategy(strategy_factory())
        return AIResponseCreator(agent).publish_response(question)
    except Exception:
        db.session.rollback()
        logger.exception(
            "El agente %r no pudo responder la pregunta %s.", agent.agent_name, question.id
        )
        return None


def trigger_agents(
    question: Question,
    strategy_factory: Callable[[], LLMStrategy] | None = None,
) -> list[Response]:
    """Hace que los agentes asociados a las etiquetas de la pregunta la respondan.

    Pensada para llamarse justo después de guardar la pregunta. Nunca lanza
    excepciones: si el LLM falla, la pregunta queda publicada y el error se registra.
    """
    factory = strategy_factory or strategy_from_env
    responses = []

    for agent in agents_for_question(question):
        if has_responded(agent, question):
            continue

        response = _publish_ai_response(agent, question, factory)
        if response is not None:
            responses.append(response)

    return responses


def respond_to_unanswered_questions(
    now: datetime | None = None,
    strategy_factory: Callable[[], LLMStrategy] | None = None,
) -> list[Response]:
    """Proceso periódico: el agente responde las preguntas que nadie contestó a tiempo.

    Los agentes se revisan del timeout más corto al más largo. Apenas uno responde,
    la pregunta deja de estar sin respuestas, así que los demás ya no intervienen.
    """
    now = now or datetime.now(UTC).replace(tzinfo=None)
    factory = strategy_factory or strategy_from_env
    responses = []

    agents = db.session.scalars(db.select(AIAgent).order_by(AIAgent.timeout_minutes, AIAgent.id))
    for agent in list(agents):
        for question in questions_waiting_for(agent, now):
            if has_responded(agent, question):
                continue

            response = _publish_ai_response(agent, question, factory)
            if response is not None:
                responses.append(response)

    return responses
