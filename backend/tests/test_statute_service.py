import pytest

from app.db.database import Base, SessionLocal, engine
from app.schemas.statute import StatuteLookupStatus, StatuteReference
from app.services.statute.references import build_label
from app.services.statute.service import resolve_reference, resolve_references
from tests.fakes import FakeEgovClient


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _reference(law_name: str, article: int, paragraph=None) -> StatuteReference:
    label = build_label(law_name, article, paragraph)
    return StatuteReference(
        raw=label,
        law_name=law_name,
        article=article,
        paragraph=paragraph,
        label=label,
        cited_by=["doc1-pro-a1"],
    )


def test_resolve_reference_fetches_and_caches(db):
    client = FakeEgovClient()
    first = resolve_reference(db, _reference("所得税法", 56), client)
    assert first.status == StatuteLookupStatus.FOUND
    assert first.caption.startswith("（事業から対価")
    assert first.from_cache is False
    assert first.source_url.endswith("#Mp-At_56")
    assert first.cited_by == ["doc1-pro-a1"]

    calls = len(client.calls)
    second = resolve_reference(db, _reference("所得税法", 56), client)
    assert second.from_cache is True
    assert len(client.calls) == calls, "キャッシュヒット時はAPIを呼ばない"


def test_resolve_reference_returns_paragraph_only(db):
    client = FakeEgovClient()
    article = resolve_reference(db, _reference("所得税法", 57, 2), client)
    assert article.text == "青色事業専従者の氏名を記載した書類を提出しなければならない。"


def test_resolve_reference_unknown_article_is_not_found(db):
    article = resolve_reference(db, _reference("所得税法", 999), FakeEgovClient())
    assert article.status == StatuteLookupStatus.NOT_FOUND
    assert article.text == ""


def test_resolve_reference_unknown_law_is_not_found(db):
    article = resolve_reference(db, _reference("架空法", 1), FakeEgovClient())
    assert article.status == StatuteLookupStatus.NOT_FOUND


def test_resolve_references_survives_api_outage(db):
    articles = resolve_references(
        db, [_reference("所得税法", 12), _reference("所得税法", 13)], FakeEgovClient(unavailable=True)
    )
    assert [a.status for a in articles] == [
        StatuteLookupStatus.UNAVAILABLE,
        StatuteLookupStatus.UNAVAILABLE,
    ]
    assert "接続できません" in articles[0].message
