"""参考資料（証拠資料集）のパースと、立論との突合。

参考資料は「Ⅰ. 関連法令 → 法令ごとの条文」「Ⅱ. 資料 → 資料N（引用と出典文献）」
という構成を想定する。立論側の【資料N参照】【法37条1項】と突き合わせ、
欠番の資料番号・未使用の資料・条文引用の差異を検出する。
"""

import re
from typing import Dict, List, Optional

from app.schemas.debate import (
    Argument,
    MaterialEntry,
    MaterialLink,
    MaterialLinkStatus,
    ReferenceCheck,
    ReferenceDocumentInput,
    ReferencePacket,
    ReferenceStatuteEntry,
    StatuteConsistency,
    StatuteConsistencyStatus,
)
from app.services.debate.parser import extract_title
from app.services.statute.references import build_label, parse_number

STATUTE_SECTION = re.compile(r"関連法令")
MATERIAL_SECTION = re.compile(r"^資料$|資料$")
ROMAN_HEADING = re.compile(r"^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+)[\.．、]\s*(.*)$")
NUMBER_HEADING = re.compile(r"^([0-9０-９]{1,2})[\.．]\s*(\S.*)$")
PAREN_HEADING = re.compile(r"^[（(]([0-9０-９]{1,2})[）)]\s*(\S.*)$")
ARTICLE_LINE = re.compile(
    r"^第([0-9０-９一二三四五六七八九十百]{1,6})条"
    r"(?:\s*第?([0-9０-９一二三四五六七八九十]{1,3})項)?[　\s]*(.*)$"
)
PARAGRAPH_LINE = re.compile(r"^([0-9０-９一二三四五六七八九十]{1,3})項[　\s]*(.*)$")
SOURCE_HINT = re.compile(r"(頁|白書|統計年報書|質問主意書|答弁第|議事録|号（|号\s*\()")
MATERIAL_CITATION = re.compile(r"資料\s*([0-9０-９]{1,2})")
QUOTE_PREFIXES = ("「", "○", "①", "②", "③", "④", "⑤", "（", "(")


def _is_source_line(line: str) -> bool:
    if line.startswith(QUOTE_PREFIXES):
        return False
    return bool(SOURCE_HINT.search(line)) and len(line) <= 200


def _clean_label(label: str) -> str:
    return label.replace("\u3000", " ").strip()


def parse_reference_packet(document: ReferenceDocumentInput) -> ReferencePacket:
    """参考資料の本文を関連法令と資料Nに分解する。"""
    section: Optional[str] = None
    law_name = ""
    statutes: List[ReferenceStatuteEntry] = []
    materials: List[MaterialEntry] = []
    current: Optional[MaterialEntry] = None
    current_statute: Optional[ReferenceStatuteEntry] = None

    for raw_line in document.text.splitlines():
        line = raw_line.replace("\u3000", " ").strip()
        if not line:
            continue

        roman = ROMAN_HEADING.match(line)
        if roman:
            heading = roman.group(2).strip()
            if STATUTE_SECTION.search(heading):
                section = "statutes"
            elif MATERIAL_SECTION.search(heading):
                section = "materials"
            else:
                section = None
            law_name = ""
            current = None
            current_statute = None
            continue

        if section == "statutes":
            number_heading = NUMBER_HEADING.match(line)
            if number_heading:
                law_name = _clean_label(number_heading.group(2))
                current_statute = None
                continue
            article_match = ARTICLE_LINE.match(line)
            if article_match:
                article = parse_number(article_match.group(1))
                paragraph = (
                    parse_number(article_match.group(2))
                    if article_match.group(2)
                    else None
                )
                if article is None:
                    continue
                current_statute = ReferenceStatuteEntry(
                    law_name=law_name or "（法令名不明）",
                    label=build_label(law_name or "（法令名不明）", article, paragraph),
                    article=article,
                    paragraph=paragraph,
                    text=article_match.group(3).strip(),
                )
                statutes.append(current_statute)
                continue
            paragraph_match = PARAGRAPH_LINE.match(line)
            if paragraph_match and current_statute is not None:
                paragraph = parse_number(paragraph_match.group(1))
                if paragraph is not None:
                    current_statute = ReferenceStatuteEntry(
                        law_name=current_statute.law_name,
                        label=build_label(
                            current_statute.law_name,
                            current_statute.article,
                            paragraph,
                        ),
                        article=current_statute.article,
                        paragraph=paragraph,
                        text=paragraph_match.group(2).strip(),
                    )
                    statutes.append(current_statute)
                    continue
            if current_statute is not None:
                current_statute.text = "".join([current_statute.text, line])
            continue

        if section == "materials":
            number_heading = NUMBER_HEADING.match(line)
            if number_heading:
                number = parse_number(number_heading.group(1))
                if number is None:
                    continue
                current = MaterialEntry(
                    number=number,
                    label=_clean_label(number_heading.group(2)),
                    sources=[],
                    excerpt="",
                )
                materials.append(current)
                continue
            if current is None:
                continue
            paren = PAREN_HEADING.match(line)
            if paren:
                current.subsections.append(_clean_label(paren.group(2)))
                continue
            if _is_source_line(line):
                if line not in current.sources:
                    current.sources.append(line)
                continue
            if len(current.excerpt) < 400:
                current.excerpt = (current.excerpt + line)[:400]

    return ReferencePacket(
        side=document.side,
        title=document.title or extract_title(document.text),
        statutes=statutes,
        materials=materials,
    )


def _normalize_statute_text(text: str) -> str:
    return re.sub(r"[\s　]", "", text)


def check_statute_consistency(
    packet: ReferencePacket, current_texts: Dict[str, str]
) -> List[StatuteConsistency]:
    """参考資料に貼られた条文と、現行条文（e-Gov）を突き合わせる。"""
    results: List[StatuteConsistency] = []
    for entry in packet.statutes:
        current = current_texts.get(entry.label) or current_texts.get(
            build_label(entry.law_name, entry.article, None)
        )
        if not current:
            results.append(
                StatuteConsistency(
                    label=entry.label,
                    packet_text=entry.text,
                    status=StatuteConsistencyStatus.UNVERIFIED,
                    note="e-Gov 法令APIで現行条文を取得できなかったため未照合です",
                )
            )
            continue
        normalized_current = _normalize_statute_text(current)
        segments = [
            _normalize_statute_text(segment)
            for segment in re.split(r"…{2,}|\.{3,}", entry.text)
            if len(_normalize_statute_text(segment)) >= 12
        ]
        missing = [
            segment for segment in segments if segment not in normalized_current
        ]
        if not segments:
            status = StatuteConsistencyStatus.UNVERIFIED
            note = "参考資料側の条文が短いため照合できません"
        elif missing:
            status = StatuteConsistencyStatus.DIFFERS
            note = f"現行条文に見当たらない語句があります: 「{missing[0][:40]}…」"
        else:
            status = StatuteConsistencyStatus.CONSISTENT
            note = "参考資料の引用は現行条文と一致します"
        results.append(
            StatuteConsistency(
                label=entry.label,
                packet_text=entry.text,
                status=status,
                note=note,
            )
        )
    return results


def build_reference_check(
    packet: ReferencePacket,
    arguments: List[Argument],
    current_texts: Optional[Dict[str, str]] = None,
) -> ReferenceCheck:
    """立論の【資料N参照】と参考資料の資料Nを突合する。"""
    cited: Dict[int, List[str]] = {}
    for argument in arguments:
        if argument.side != packet.side:
            continue
        for citation in argument.citations:
            match = MATERIAL_CITATION.search(citation.label)
            if not match:
                continue
            number = parse_number(match.group(1))
            if number is None:
                continue
            cited.setdefault(number, [])
            if argument.id not in cited[number]:
                cited[number].append(argument.id)

    by_number = {entry.number: entry for entry in packet.materials}
    links: List[MaterialLink] = []
    for number in sorted(set(by_number) | set(cited)):
        entry = by_number.get(number)
        cited_by = cited.get(number, [])
        if entry is None:
            status = MaterialLinkStatus.MISSING
            note = "立論が引用していますが、参考資料に該当する資料番号がありません"
        elif not cited_by:
            status = MaterialLinkStatus.UNUSED
            note = "参考資料に載っていますが、立論から引用されていません"
        else:
            status = MaterialLinkStatus.LINKED
            note = (
                ""
                if entry.sources
                else "出典文献（著者・書名・頁）を読み取れませんでした"
            )
        links.append(
            MaterialLink(
                number=number,
                label=entry.label if entry else "",
                sources=entry.sources if entry else [],
                subsections=entry.subsections if entry else [],
                cited_by=cited_by,
                status=status,
                note=note,
            )
        )

    return ReferenceCheck(
        side=packet.side,
        packet_title=packet.title,
        material_links=links,
        missing_numbers=[
            link.number for link in links if link.status == MaterialLinkStatus.MISSING
        ],
        unused_numbers=[
            link.number for link in links if link.status == MaterialLinkStatus.UNUSED
        ],
        statute_consistency=check_statute_consistency(packet, current_texts or {}),
    )
