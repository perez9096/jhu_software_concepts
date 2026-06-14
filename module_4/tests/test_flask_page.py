import sys
from pathlib import Path
import pytest

pytestmark = pytest.mark.web

MODULE_4_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = MODULE_4_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from query_data import app


@pytest.fixture
def client():
    app.config.update({
        "TESTING": True,
    })

    with app.test_client() as client:
        yield client


def test_app_has_required_routes():
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    assert "/" in routes
    assert "/analysis" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes



def test_get_analysis_page_loads(client):
    response = client.get("/analysis")

    assert response.status_code == 200


def test_analysis_page_contains_buttons(client):
    response = client.get("/analysis")
    page_text = response.data.decode("utf-8")

    assert "Pull Data" in page_text
    assert "Update Analysis" in page_text


def test_analysis_page_contains_required_text(client):
    response = client.get("/analysis")
    page_text = response.data.decode("utf-8")

    assert "Analysis" in page_text
    assert "Answer:" in page_text