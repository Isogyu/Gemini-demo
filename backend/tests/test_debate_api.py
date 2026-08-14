import io

import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.db.database import Base, engine
from app.main import app
from app.services.statute.egov import get_egov_client
from tests.fakes import FakeEgovClient


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(setup_database):
    app.dependency_overrides[get_egov_client] = FakeEgovClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_egov_client, None)


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
        json={
            "documents": sample["documents"],
            "topic": sample["topic"],
            "resolve_statutes": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["documents"]) == 2
    assert body["issues"]
    assert body["rebuttals"]
    assert body["statutes"] == []
    assert "所得税法第56条" in [r["label"] for r in body["statute_references"]]


def test_analyze_sample_resolves_statutes_and_references(client):
    sample = client.get("/api/debate/samples/income-tax-56-57").json()
    response = client.post(
        "/api/debate/analyze",
        json={
            "documents": sample["documents"],
            "references": sample["references"],
            "topic": sample["topic"],
        },
    )
    assert response.status_code == 200
    body = response.json()

    statutes = {s["label"]: s for s in body["statutes"]}
    assert statutes["所得税法第56条"]["status"] == "found"
    assert "必要経費に算入しない" in statutes["所得税法第56条"]["text"]
    assert statutes["所得税法第56条"]["source_url"].startswith("https://laws.e-gov.go.jp/")
    # ダミークライアントが知らない法令は not_found として返り、解析自体は成功する
    assert statutes["税制改革法第3条"]["status"] == "not_found"

    checks = {c["side"]: c for c in body["reference_checks"]}
    assert set(checks) == {"pro", "con"}
    assert [link["number"] for link in checks["pro"]["material_links"]] == list(
        range(1, 11)
    )
    assert checks["pro"]["missing_numbers"] == []
    assert checks["pro"]["unused_numbers"] == []
    consistency = {c["label"]: c for c in checks["pro"]["statute_consistency"]}
    # ダミークライアントは要約した条文を返すため、参考資料の引用との差異が検出される
    assert consistency["所得税法第56条"]["status"] == "differs"
    assert consistency["所得税法第56条"]["note"]
    con_consistency = {c["label"]: c for c in checks["con"]["statute_consistency"]}
    # 条文を取得できなかった法令は「未照合」として明示する
    assert con_consistency["税制改革法第3条"]["status"] == "unverified"


def test_statute_article_endpoint(client):
    response = client.get(
        "/api/statutes/article", params={"law_name": "所得税法", "article": 57, "paragraph": 1}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "found"
    assert body["label"] == "所得税法第57条第1項"
    assert body["text"].startswith("青色事業専従者")


def test_statute_resolve_endpoint_extracts_references(client):
    response = client.post(
        "/api/statutes/resolve",
        json={"text": "56条および57条は必要経費算入を制限する。"},
    )
    assert response.status_code == 200
    assert [s["label"] for s in response.json()] == ["所得税法第56条", "所得税法第57条"]


def test_analyze_persists_history(client):
    sample = client.get("/api/debate/samples/income-tax-56-57").json()
    client.post(
        "/api/debate/analyze",
        json={
            "documents": sample["documents"],
            "topic": sample["topic"],
            "resolve_statutes": False,
        },
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
