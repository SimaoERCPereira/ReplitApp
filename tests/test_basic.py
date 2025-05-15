import pytest
from app_production import app

def test_home_page():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200 