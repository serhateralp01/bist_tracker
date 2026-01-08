from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main, portfolio, transactions, analysis
    app.register_blueprint(main.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(analysis.bp)

    return app
