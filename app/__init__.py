from flask import Flask

from app.blueprints.questions.routes import bp as questions_bp
from app.blueprints.responses.routes import bp as responses_bp
from app.blueprints.users.routes import bp as users_bp
from app.blueprints.votes.routes import bp as votes_bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    if config:
        app.config.update(config)

    app.register_blueprint(users_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(responses_bp)
    app.register_blueprint(votes_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app