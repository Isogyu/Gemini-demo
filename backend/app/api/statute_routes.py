"""法令条文の参照API（e-Gov 法令API のプロキシ＋キャッシュ）。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.statute import (
    StatuteArticle,
    StatuteReference,
    StatuteResolveRequest,
)
from app.services.statute.egov import EgovClient, get_egov_client
from app.services.statute.references import (
    DEFAULT_LAW_NAME,
    build_label,
    extract_statute_references,
)
from app.services.statute.service import resolve_reference, resolve_references

router = APIRouter(prefix="/statutes", tags=["statutes"])


@router.get("/article", response_model=StatuteArticle)
def read_article(
    law_name: str = Query(default=DEFAULT_LAW_NAME, description="法令名（例: 所得税法）"),
    article: int = Query(ge=1, description="条番号"),
    paragraph: Optional[int] = Query(default=None, ge=1, description="項番号"),
    db: Session = Depends(get_db),
    egov: EgovClient = Depends(get_egov_client),
) -> StatuteArticle:
    """条文を1件取得する（キャッシュ優先）。"""
    reference = StatuteReference(
        raw=build_label(law_name, article, paragraph),
        law_name=law_name,
        article=article,
        paragraph=paragraph,
        label=build_label(law_name, article, paragraph),
    )
    return resolve_reference(db, reference, egov)


@router.post("/resolve", response_model=List[StatuteArticle])
def resolve_from_text(
    payload: StatuteResolveRequest,
    db: Session = Depends(get_db),
    egov: EgovClient = Depends(get_egov_client),
) -> List[StatuteArticle]:
    """本文中の法令参照を抽出し、条文をまとめて取得する。"""
    references = extract_statute_references(payload.text, payload.default_law_name)
    return resolve_references(db, references, egov)
