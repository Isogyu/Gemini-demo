"""法令参照（e-Gov 法令API）の入出力スキーマ。"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class StatuteReference(BaseModel):
    """立論本文から抽出した法令参照。"""

    raw: str = Field(description="本文中の表記（例: 法37条1項）")
    law_name: str = Field(description="正規化した法令名")
    article: int
    paragraph: Optional[int] = None
    label: str = Field(description="所得税法第56条第1項 のような正規化表記")
    cited_by: List[str] = Field(default_factory=list, description="参照元の論証ブロックID")


class StatuteResolveRequest(BaseModel):
    """本文から法令参照を抽出して条文を取得するリクエスト。"""

    text: str
    default_law_name: str = "所得税法"


class StatuteLookupStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"


class StatuteArticle(BaseModel):
    """e-Gov 法令APIから取得した条文。"""

    label: str
    law_name: str
    law_num: str = ""
    law_id: str = ""
    article: int
    paragraph: Optional[int] = None
    caption: str = ""
    text: str = ""
    source_url: str = ""
    fetched_at: Optional[datetime] = None
    from_cache: bool = False
    status: StatuteLookupStatus
    message: str = ""
    cited_by: List[str] = Field(default_factory=list)
