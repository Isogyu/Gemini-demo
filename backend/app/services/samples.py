"""サンプル試算表データセットの読み込み。"""

import json
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseModel

from app.schemas.tax import (
    DepreciationAssetInput,
    EntertainmentInput,
    ReconciliationRequest,
    TrialBalance,
)

SAMPLES_PATH = Path(__file__).resolve().parent.parent / "data" / "samples.json"


class SampleDataset(BaseModel):
    id: str
    label: str
    company_name: str
    fiscal_year: int
    capital: float
    trial_balance: TrialBalance
    entertainment: EntertainmentInput
    depreciation_assets: List[DepreciationAssetInput]
    other_additions: float = 0.0
    other_subtractions: float = 0.0

    def to_request(self) -> ReconciliationRequest:
        return ReconciliationRequest(
            company_name=self.company_name,
            fiscal_year=self.fiscal_year,
            capital=self.capital,
            trial_balance=self.trial_balance,
            entertainment=self.entertainment,
            depreciation_assets=self.depreciation_assets,
            other_additions=self.other_additions,
            other_subtractions=self.other_subtractions,
        )


@lru_cache(maxsize=1)
def load_samples() -> List[SampleDataset]:
    raw = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    return [SampleDataset.model_validate(item) for item in raw]


def get_sample(sample_id: str) -> SampleDataset:
    for sample in load_samples():
        if sample.id == sample_id:
            return sample
    raise KeyError(sample_id)
