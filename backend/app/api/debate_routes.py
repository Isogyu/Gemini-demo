import json
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DebateAnalysisRun
from app.schemas.debate import (
    DebateAnalysis,
    DebateAnalysisRequest,
    DebateSample,
    ExtractedDocument,
)
from app.services.debate.analysis import analyze, attach_statutes
from app.services.debate.extractor import UnsupportedFileError, extract_document
from app.services.debate.samples import get_debate_sample, load_debate_samples
from app.services.statute.egov import EgovClient, get_egov_client
from app.services.statute.service import resolve_references

router = APIRouter(prefix="/debate", tags=["debate"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.get("/samples", response_model=List[DebateSample])
def list_debate_samples() -> List[DebateSample]:
    return load_debate_samples()


@router.get("/samples/{sample_id}", response_model=DebateSample)
def read_debate_sample(sample_id: str) -> DebateSample:
    try:
        return get_debate_sample(sample_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="sample not found")


@router.post("/extract", response_model=ExtractedDocument)
async def extract(file: UploadFile = File(...)) -> ExtractedDocument:
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="ファイルサイズが大きすぎます（上限 5MB）")
    try:
        return extract_document(file.filename or "", content)
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/analyze", response_model=DebateAnalysis)
def create_analysis(
    request: DebateAnalysisRequest,
    db: Session = Depends(get_db),
    egov: EgovClient = Depends(get_egov_client),
) -> DebateAnalysis:
    try:
        result = analyze(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if request.resolve_statutes and result.statute_references:
        attach_statutes(
            result,
            request,
            resolve_references(db, result.statute_references, egov),
        )

    db.add(
        DebateAnalysisRun(
            topic=result.topic,
            document_count=len(result.documents),
            issue_count=len(result.issues),
            rebuttal_count=len(result.rebuttals),
            result_payload=result.model_dump_json(),
        )
    )
    db.commit()
    return result


@router.get("/history", response_model=List[DebateAnalysis])
def list_analysis_history(
    limit: int = 20, db: Session = Depends(get_db)
) -> List[DebateAnalysis]:
    rows = db.scalars(
        select(DebateAnalysisRun).order_by(DebateAnalysisRun.id.desc()).limit(limit)
    ).all()
    return [DebateAnalysis.model_validate(json.loads(r.result_payload)) for r in rows]
