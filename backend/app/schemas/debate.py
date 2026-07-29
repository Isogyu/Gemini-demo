"""ディベート立論分析（論点マップ・反駁生成）の入出力スキーマ。"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Side(str, Enum):
    """立論の立場。"""

    PRO = "pro"
    CON = "con"


class CitationKind(str, Enum):
    MATERIAL = "material"
    STATUTE = "statute"
    CASE = "case"
    OTHER = "other"


class Citation(BaseModel):
    raw: str = Field(description="本文中の引用表記（【】内を含む）")
    label: str = Field(description="正規化した出典名")
    kind: CitationKind


class Argument(BaseModel):
    """立論を構成する最小単位（見出しごとの論証ブロック）。"""

    id: str
    side: Side
    document_id: str
    section: str = Field(description="Ⅱ.1.(1) のような節番号")
    heading: str
    text: str
    claim: str = Field(description="ブロックの結論にあたる一文")
    citations: List[Citation] = []
    issue_ids: List[str] = []
    warnings: List[str] = []


class IssueStance(BaseModel):
    side: Side
    argument_ids: List[str]
    points: List[str] = Field(description="そのサイドの主張要旨")
    citation_count: int


class ClashStatus(str, Enum):
    CLASH = "clash"
    PRO_ONLY = "pro_only"
    CON_ONLY = "con_only"
    ABSENT = "absent"


class IssueClash(BaseModel):
    """一つの争点についての賛否の対置。"""

    issue_id: str
    label: str
    description: str
    status: ClashStatus
    pro: Optional[IssueStance] = None
    con: Optional[IssueStance] = None
    note: str = ""


class RebuttalStrength(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Rebuttal(BaseModel):
    """反駁候補と、それを支える想定尋問。"""

    id: str
    pattern_id: str
    target_side: Side = Field(description="この反駁が攻撃する側")
    issue_id: str
    issue_label: str
    title: str
    body: str
    trigger: str = Field(description="反駁の起点となった相手立論の文言")
    cross_examination: List[str] = []
    strength: RebuttalStrength


class DocumentSummary(BaseModel):
    id: str
    side: Side
    title: str
    char_count: int
    argument_count: int
    citation_count: int


class EvidenceReport(BaseModel):
    """出典の付き方に関する検査結果。"""

    document_id: str
    side: Side
    materials: List[str]
    statutes: List[str]
    cases: List[str]
    unsupported_argument_ids: List[str] = Field(
        description="出典が一つも付されていない論証ブロック"
    )


class DebateDocumentInput(BaseModel):
    side: Side
    title: str = ""
    text: str


class DebateAnalysisRequest(BaseModel):
    documents: List[DebateDocumentInput] = Field(min_length=1, max_length=2)
    topic: str = ""


class DebateAnalysis(BaseModel):
    topic: str
    documents: List[DocumentSummary]
    arguments: List[Argument]
    issues: List[IssueClash]
    rebuttals: List[Rebuttal]
    evidence: List[EvidenceReport]


class ExtractedDocument(BaseModel):
    """アップロードされたファイルから取り出した本文。"""

    title: str
    text: str
    detected_side: Optional[Side] = None


class DebateSample(BaseModel):
    id: str
    label: str
    topic: str
    documents: List[DebateDocumentInput]
