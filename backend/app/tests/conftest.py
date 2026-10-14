import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment
os.environ["ALLOW_DEV_FAULT_INJECTION"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_aurora.db"

from app.db.session import Base, get_db
from app.main import app
from app.db import init_db
from app.services.scenario_service import ScenarioService
from app.services.systems_engineering_service import SystemsEngineeringService
from app.services.simulation_engine import simulator

TEST_DATABASE_URL = "sqlite:///./test_aurora.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    ScenarioService.seed_default_scenarios(db)
    SystemsEngineeringService.seed_initial_records(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_aurora.db"):
        try:
            os.remove("./test_aurora.db")
        except Exception:
            pass

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
