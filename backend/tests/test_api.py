import pytest
from fastapi.testclient import TestClient

from app.db.database import Base, engine
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(setup_database):
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_list_samples(client):
    response = client.get("/api/samples")
    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert "sme-2025" in ids


def test_get_unknown_sample_returns_404(client):
    assert client.get("/api/samples/unknown").status_code == 404


def test_reconciliation_endpoint_returns_result_and_persists_history(client):
    sample = client.get("/api/samples/sme-2025").json()
    payload = {
        "company_name": sample["company_name"],
        "fiscal_year": sample["fiscal_year"],
        "capital": sample["capital"],
        "trial_balance": sample["trial_balance"],
        "entertainment": sample["entertainment"],
        "depreciation_assets": sample["depreciation_assets"],
    }
    response = client.post("/api/reconciliation", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["taxable_income"] == 24_800_000
    assert body["tax"]["total_tax"] > 0

    history = client.get("/api/reconciliation/history").json()
    assert len(history) >= 1
    assert history[0]["company_name"] == sample["company_name"]


def test_reconciliation_requires_income_source(client):
    response = client.post("/api/reconciliation", json={"capital": 10_000_000})
    assert response.status_code == 422
