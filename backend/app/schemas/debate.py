"""ディベート立論分析（論点マップ・反駁生成）の入出力スキーマ。"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.statute import StatuteArticle, StatuteReference


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


class ReferenceStatuteEntry(BaseModel):
    """参考資料の「関連法令」に貼られた条文。"""

    law_name: str
    label: str
    article: int
    paragraph: Optional[int] = None
    text: str = ""


class MaterialEntry(BaseModel):
    """参考資料の「資料N」。"""

    number: int
    label: str
    sources: List[str] = Field(default_factory=list, description="出典文献（著者・書名・頁）")
    subsections: List[str] = Field(default_factory=list)
    excerpt: str = ""


class ReferencePacket(BaseModel):
    side: Side
    title: str
    statutes: List[ReferenceStatuteEntry] = Field(default_factory=list)
    materials: List[MaterialEntry] = Field(default_factory=list)


class MaterialLinkStatus(str, Enum):
    LINKED = "linked"
    MISSING = "missing"
    UNUSED = "unused"


class MaterialLink(BaseModel):
    """立論の【資料N参照】と参考資料の資料Nの対応。"""

    number: int
    label: str = ""
    sources: List[str] = Field(default_factory=list)
    subsections: List[str] = Field(default_factory=list)
    cited_by: List[str] = Field(default_factory=list)
    status: MaterialLinkStatus
    note: str = ""


class StatuteConsistencyStatus(str, Enum):
    CONSISTENT = "consistent"
    DIFFERS = "differs"
    UNVERIFIED = "unverified"


class StatuteConsistency(BaseModel):
    """参考資料に引用された条文と現行条文の照合結果。"""

    label: str
    packet_text: str
    status: StatuteConsistencyStatus
    note: str = ""


class ReferenceCheck(BaseModel):
    side: Side
    packet_title: str
    material_links: List[MaterialLink] = Field(default_factory=list)
    missing_numbers: List[int] = Field(default_factory=list)
    unused_numbers: List[int] = Field(default_factory=list)
    statute_consistency: List[StatuteConsistency] = Field(default_factory=list)


class DebateDocumentInput(BaseModel):
    side: Side
    title: str = ""
    text: str


class ReferenceDocumentInput(BaseModel):
    """参考資料（証拠資料集）の入力。"""

    side: Side
    title: str = ""
    text: str


class DebateAnalysisRequest(BaseModel):
    documents: List[DebateDocumentInput] = Field(min_length=1, max_length=2)
    references: List[ReferenceDocumentInput] = Field(default_factory=list, max_length=2)
    topic: str = ""
    resolve_statutes: bool = Field(
        default=True, description="e-Gov 法令APIで条文を自動取得するか"
    )
    default_law_name: str = Field(
        default="所得税法", description="「法○条」のように法令名が省略された場合の補完先"
    )


class DebateAnalysis(BaseModel):
    topic: str
    documents: List[DocumentSummary]
    arguments: List[Argument]
    issues: List[IssueClash]
    rebuttals: List[Rebuttal]
    evidence: List[EvidenceReport]
    statute_references: List[StatuteReference] = Field(default_factory=list)
    statutes: List[StatuteArticle] = Field(default_factory=list)
    reference_checks: List[ReferenceCheck] = Field(default_factory=list)


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
    references: List[ReferenceDocumentInput] = Field(default_factory=list)
