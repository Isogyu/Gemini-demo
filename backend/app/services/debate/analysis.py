"""立論の構造化・論点マップ・反駁生成を束ねるエントリポイント。"""

from typing import List

from app.schemas.debate import (
    Argument,
    CitationKind,
    DebateAnalysis,
    DebateAnalysisRequest,
    DocumentSummary,
    EvidenceReport,
)
from app.services.debate.issues import assign_issues, build_issue_map
from app.services.debate.parser import extract_title, parse_document
from app.services.debate.rebuttal import generate_rebuttals

UNSUPPORTED_MIN_LENGTH = 80


def _evidence_report(
    document_id: str, arguments: List[Argument]
) -> EvidenceReport:
    materials: List[str] = []
    statutes: List[str] = []
    cases: List[str] = []
    for argument in arguments:
        for citation in argument.citations:
            bucket = {
                CitationKind.MATERIAL: materials,
                CitationKind.STATUTE: statutes,
                CitationKind.CASE: cases,
            }.get(citation.kind)
            if bucket is not None and citation.label not in bucket:
                bucket.append(citation.label)
    return EvidenceReport(
        document_id=document_id,
        side=arguments[0].side,
        materials=materials,
        statutes=statutes,
        cases=cases,
        unsupported_argument_ids=[
            a.id
            for a in arguments
            if not a.citations and len(a.text) >= UNSUPPORTED_MIN_LENGTH
        ],
    )


def analyze(request: DebateAnalysisRequest) -> DebateAnalysis:
    """立論テキストを解析し、論点マップと反駁候補を返す。"""
    all_arguments: List[Argument] = []
    summaries: List[DocumentSummary] = []
    evidence: List[EvidenceReport] = []

    for index, document in enumerate(request.documents, start=1):
        if not document.text.strip():
            raise ValueError("立論の本文が空です")
        document_id = f"doc{index}-{document.side.value}"
        arguments = parse_document(document_id, document.side, document.text)
        if not arguments:
            raise ValueError(
                "論証ブロックを検出できませんでした。"
                "「Ⅰ.」「1.」「（1）」のような見出しを含む立論を入力してください"
            )
        for argument in arguments:
            argument.issue_ids = assign_issues(argument)
        all_arguments.extend(arguments)
        summaries.append(
            DocumentSummary(
                id=document_id,
                side=document.side,
                title=document.title or extract_title(document.text),
                char_count=len(document.text),
                argument_count=len(arguments),
                citation_count=sum(len(a.citations) for a in arguments),
            )
        )
        evidence.append(_evidence_report(document_id, arguments))

    issues = build_issue_map(all_arguments)
    return DebateAnalysis(
        topic=request.topic or "（論題未設定）",
        documents=summaries,
        arguments=all_arguments,
        issues=issues,
        rebuttals=generate_rebuttals(all_arguments, issues),
        evidence=evidence,
    )
