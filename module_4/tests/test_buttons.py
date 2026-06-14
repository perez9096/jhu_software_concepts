import sys
from pathlib import Path
from unittest.mock import patch
import pytest

pytestmark = pytest.mark.buttons

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = MODULE_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import query_data


@pytest.fixture
def client():
    query_data.app.config.update(TESTING=True)

    with query_data.app.test_client() as client:
        yield client


def test_pull_data_returns_200_and_triggers_loader(client):
    with patch.object(query_data, "_run_scraper_and_load") as mock_loader:
        response = client.post("/pull-data", follow_redirects=True)

    assert response.status_code == 200
    assert mock_loader.called

def test_update_analysis_returns_200_when_not_busy(client):
    with patch.object(query_data, "is_scrape_running", return_value=False):
        response = client.post("/update-analysis", follow_redirects=True)

    assert response.status_code == 200


def test_update_analysis_returns_409_when_busy(client):
    with patch.object(query_data, "is_scrape_running", return_value=True):
        response = client.post("/update-analysis")

    assert response.status_code == 409


def test_pull_data_returns_409_when_busy(client):
    with patch.object(query_data, "is_scrape_running", return_value=True):
        response = client.post("/pull-data")

    assert response.status_code == 409