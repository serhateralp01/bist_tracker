import pytest
from backend.app import app
from backend.database import Base, engine, SessionLocal
from backend import models

@pytest.fixture(scope="module")
def test_client():
    # Set up
    Base.metadata.create_all(bind=engine)
    app.config['TESTING'] = True

    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client

    # Teardown
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
