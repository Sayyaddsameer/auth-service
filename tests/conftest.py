import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def client():
    # We use the TestClient which runs the app without starting a real server
    with TestClient(app) as c:
        yield c