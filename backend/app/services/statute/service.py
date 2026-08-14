"""法令参照の解決（キャッシュ優先 + e-Gov 法令API）。"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StatuteArticleCache
from app.schemas.statute import (
    StatuteArticle,
    StatuteLookupStatus,
    StatuteReference,
)
from app.services.statute.egov import (
    EgovClient,
    EgovUnavailableError,
    LawNotFoundError,
    law_page_url,
)

CACHE_TTL = timedelta(days=30)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _paragraph_text(text: str, paragraph: Optional[int]) -> str:
    """項番号が指定されていれば当該項のみを返す。"""
    if not paragraph:
        return text
    paragraphs = text.split("\n\n")
    if 0 < paragraph <= len(paragraphs):
        return paragraphs[paragraph - 1]
    return text


def _to_article(
    reference: StatuteReference, row: StatuteArticleCache, from_cache: bool
) -> StatuteArticle:
    return StatuteArticle(
        label=reference.label,
        law_name=row.law_name,
        law_num=row.law_num,
        law_id=row.law_id,
        article=reference.article,
        paragraph=reference.paragraph,
        caption=row.caption,
        text=_paragraph_text(row.text, reference.paragraph),
        source_url=law_page_url(row.law_id, reference.article),
        fetched_at=_as_aware(row.fetched_at),
        from_cache=from_cache,
        status=StatuteLookupStatus.FOUND,
        cited_by=list(reference.cited_by),
    )


def _find_cached(
    db: Session, law_name: str, article: int
) -> Optional[StatuteArticleCache]:
    row = db.scalar(
        select(StatuteArticleCache).where(
            StatuteArticleCache.law_name == law_name,
            StatuteArticleCache.article == article,
        )
    )
    if row is None:
        return None
    if _utcnow() - _as_aware(row.fetched_at) > CACHE_TTL:
        return None
    return row


def resolve_reference(
    db: Session, reference: StatuteReference, client: EgovClient
) -> StatuteArticle:
    """一つの法令参照を条文へ解決する（キャッシュ優先）。"""
    cached = _find_cached(db, reference.law_name, reference.article)
    if cached is not None:
        return _to_article(reference, cached, from_cache=True)

    try:
        law = client.find_law(reference.law_name)
        content = client.fetch_article(law.law_num, reference.article)
    except LawNotFoundError:
        return StatuteArticle(
            label=reference.label,
            law_name=reference.law_name,
            article=reference.article,
            paragraph=reference.paragraph,
            status=StatuteLookupStatus.NOT_FOUND,
            message="e-Gov 法令データベースに該当する条文が見つかりませんでした",
            cited_by=list(reference.cited_by),
        )
    except EgovUnavailableError as exc:
        return StatuteArticle(
            label=reference.label,
            law_name=reference.law_name,
            article=reference.article,
            paragraph=reference.paragraph,
            status=StatuteLookupStatus.UNAVAILABLE,
            message=str(exc),
            cited_by=list(reference.cited_by),
        )

    row = StatuteArticleCache(
        law_name=reference.law_name,
        law_num=law.law_num,
        law_id=law.law_id,
        article=reference.article,
        caption=content.caption,
        text="\n\n".join(content.paragraph_texts),
        fetched_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    return _to_article(reference, row, from_cache=False)


def resolve_references(
    db: Session,
    references: List[StatuteReference],
    client: Optional[EgovClient] = None,
) -> List[StatuteArticle]:
    active = client or EgovClient()
    return [resolve_reference(db, reference, active) for reference in references]
