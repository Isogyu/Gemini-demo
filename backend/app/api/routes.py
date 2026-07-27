import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ReconciliationRun
from app.schemas.tax import ReconciliationRequest, ReconciliationResult
from app.services.reconciliation import run_reconciliation
from app.services.samples import SampleDataset, get_sample, load_samples

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/samples", response_model=List[SampleDataset])
def list_samples() -> List[SampleDataset]:
    return load_samples()


@router.get("/samples/{sample_id}", response_model=SampleDataset)
def read_sample(sample_id: str) -> SampleDataset:
    try:
        return get_sample(sample_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="sample not found")


@router.post("/reconciliation", response_model=ReconciliationResult)
def create_reconciliation(
    request: ReconciliationRequest, db: Session = Depends(get_db)
) -> ReconciliationResult:
    try:
        result = run_reconciliation(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db.add(
        ReconciliationRun(
            company_name=result.company_name,
            fiscal_year=result.fiscal_year,
            net_income_before_tax=result.net_income_before_tax,
            taxable_income=result.taxable_income,
            total_tax=result.tax.total_tax,
            after_tax_profit=result.after_tax_profit,
            request_payload=request.model_dump_json(),
            result_payload=result.model_dump_json(),
        )
    )
    db.commit()
    return result


@router.get("/reconciliation/history", response_model=List[ReconciliationResult])
def list_history(
    limit: int = 20, db: Session = Depends(get_db)
) -> List[ReconciliationResult]:
    rows = db.scalars(
        select(ReconciliationRun).order_by(ReconciliationRun.id.desc()).limit(limit)
    ).all()
    return [ReconciliationResult.model_validate(json.loads(r.result_payload)) for r in rows]
