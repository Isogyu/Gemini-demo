"""立論の構造化・論点マップ・反駁生成を束ねるエントリポイント。"""

from typing import Dict, List

from app.schemas.debate import (
    Argument,
    CitationKind,
    DebateAnalysis,
    DebateAnalysisRequest,
    DocumentSummary,
    EvidenceReport,
    ReferenceCheck,
    ReferencePacket,
)
from app.schemas.statute import (
    StatuteArticle,
    StatuteLookupStatus,
    StatuteReference,
)
from app.services.debate.issues import assign_issues, build_issue_map
from app.services.debate.materials import (
    build_reference_check,
    parse_reference_packet,
)
from app.services.debate.parser import (
    UNSUPPORTED_MIN_LENGTH,
    extract_title,
    parse_document,
)
from app.services.debate.rebuttal import generate_rebuttals
from app.services.statute.references import build_label, extract_statute_references


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


def _reference_packets(request: DebateAnalysisRequest) -> List[ReferencePacket]:
    return [
        parse_reference_packet(document)
        for document in request.references
        if document.text.strip()
    ]


def collect_statute_references(
    arguments: List[Argument],
    packets: List[ReferencePacket],
    default_law_name: str,
) -> List[StatuteReference]:
    """立論と参考資料から法令参照を集約する（参照元IDを保持）。"""
    merged: Dict[str, StatuteReference] = {}
    for argument in arguments:
        for reference in extract_statute_references(argument.text, default_law_name):
            existing = merged.get(reference.label)
            if existing is None:
                reference.cited_by = [argument.id]
                merged[reference.label] = reference
            elif argument.id not in existing.cited_by:
                existing.cited_by.append(argument.id)

    for packet in packets:
        for entry in packet.statutes:
            article_label = build_label(entry.law_name, entry.article, None)
            if article_label in merged or entry.label in merged:
                continue
            merged[article_label] = StatuteReference(
                raw=entry.label,
                law_name=entry.law_name,
                article=entry.article,
                label=article_label,
            )
    return list(merged.values())


def statute_text_map(statutes: List[StatuteArticle]) -> Dict[str, str]:
    """条文照合用に {正規化ラベル: 条文本文} を作る。"""
    texts: Dict[str, str] = {}
    for statute in statutes:
        if statute.status != StatuteLookupStatus.FOUND:
            continue
        texts.setdefault(statute.label, statute.text)
        article_label = build_label(statute.law_name, statute.article, None)
        texts.setdefault(article_label, statute.text)
    return texts


def build_reference_checks(
    packets: List[ReferencePacket],
    arguments: List[Argument],
    statutes: List[StatuteArticle],
) -> List[ReferenceCheck]:
    texts = statute_text_map(statutes)
    return [
        build_reference_check(packet, arguments, texts) for packet in packets
    ]


def attach_statutes(
    analysis: DebateAnalysis,
    request: DebateAnalysisRequest,
    statutes: List[StatuteArticle],
) -> DebateAnalysis:
    """条文取得結果を解析結果へ反映し、参考資料の照合をやり直す。"""
    analysis.statutes = statutes
    analysis.reference_checks = build_reference_checks(
        _reference_packets(request), analysis.arguments, statutes
    )
    return analysis


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
    packets = _reference_packets(request)
    references = collect_statute_references(
        all_arguments, packets, request.default_law_name
    )
    return DebateAnalysis(
        topic=request.topic or "（論題未設定）",
        documents=summaries,
        arguments=all_arguments,
        issues=issues,
        rebuttals=generate_rebuttals(all_arguments, issues),
        evidence=evidence,
        statute_references=references,
        statutes=[],
        reference_checks=build_reference_checks(packets, all_arguments, []),
    )
