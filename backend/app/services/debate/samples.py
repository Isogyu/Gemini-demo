"""デモ用のサンプル立論の読み込み。"""

import json
from functools import lru_cache
from pathlib import Path
from typing import List

from app.schemas.debate import DebateSample

SAMPLES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "debate_samples.json"
)


@lru_cache(maxsize=1)
def load_debate_samples() -> List[DebateSample]:
    raw = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    return [DebateSample.model_validate(item) for item in raw]


def get_debate_sample(sample_id: str) -> DebateSample:
    for sample in load_debate_samples():
        if sample.id == sample_id:
            return sample
    raise KeyError(sample_id)
