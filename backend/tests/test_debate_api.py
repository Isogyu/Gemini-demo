import io

import pytest
from docx import Document
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


def _docx_bytes(lines):
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_list_debate_samples(client):
    response = client.get("/api/debate/samples")
    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == ["income-tax-56-57"]


def test_read_unknown_sample_returns_404(client):
    assert client.get("/api/debate/samples/unknown").status_code == 404


def test_analyze_sample(client):
    sample = client.get("/api/debate/samples/income-tax-56-57").json()
    response = client.post(
        "/api/debate/analyze",
        json={"documents": sample["documents"], "topic": sample["topic"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["documents"]) == 2
    assert body["issues"]
    assert body["rebuttals"]


def test_analyze_persists_history(client):
    sample = client.get("/api/debate/samples/income-tax-56-57").json()
    client.post(
        "/api/debate/analyze",
        json={"documents": sample["documents"], "topic": sample["topic"]},
    )
    history = client.get("/api/debate/history").json()
    assert len(history) >= 1
    assert history[0]["issues"]


def test_analyze_rejects_unstructured_text(client):
    response = client.post(
        "/api/debate/analyze",
        json={"documents": [{"side": "pro", "text": "見出しのない文章です。"}]},
    )
    assert response.status_code == 422


def test_extract_docx_detects_side(client):
    content = _docx_bytes(["廃止反対側立論", "Ⅰ. 主張", "廃止するべきでない。"])
    response = client.post(
        "/api/debate/extract",
        files={
            "file": (
                "con.docx",
                content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detected_side"] == "con"
    assert "廃止するべきでない" in body["text"]


def test_extract_rejects_unsupported_extension(client):
    response = client.post(
        "/api/debate/extract",
        files={"file": ("argument.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 422
