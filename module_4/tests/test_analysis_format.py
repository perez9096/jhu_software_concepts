import sys
from pathlib import Path
import re
import pytest

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = MODULE_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from query_data import app

pytestmark = pytest.mark.analysis


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

@pytest.mark.analysis
def test_answer_labels_present(client):
    response = client.get("/analysis")

    assert response.status_code == 200

    page = response.data.decode("utf-8")

    assert "Answer:" in page

@pytest.mark.analysis
def test_percentages_have_two_decimals(client):
    response = client.get("/analysis")

    page = response.data.decode("utf-8")

    matches = re.findall(r"\d+\.\d{2}%", page)

    assert len(matches) >= 1