"""立論テキストを論証ブロック（Argument）へ構造化する。

日本語のディベート立論・法律文書で慣用される見出し（Ⅰ. / 1. / （1））と、
【】による出典表記を手掛かりに、規則ベースで解析する。
"""

import re
from typing import List, Optional, Tuple

from app.schemas.debate import Argument, Citation, CitationKind, Side

ROMAN_HEADING = re.compile(r"^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+)[\.．、]\s*(.*)$")
NUMBER_HEADING = re.compile(r"^([0-9０-９]{1,2})[\.．]\s*(\S.*)$")
PAREN_HEADING = re.compile(r"^[（(]([0-9０-９]{1,2})[）)]\s*(\S.*)$")
CITATION = re.compile(r"【([^】]+)】")
SENTENCE_SPLIT = re.compile(r"(?<=。)")
MIN_BLOCK_LENGTH = 12
#: この長さ未満のブロックは要旨・結論とみなし、出典欠落の警告対象から除く。
UNSUPPORTED_MIN_LENGTH = 80

CLAIM_MARKERS = ("といえる", "べきである", "べきでない", "といえよう", "適当である", "評価せざるを得ない")
STATUTE_HINT = re.compile(r"(憲法|法|条|税制改革法)")
CASE_HINT = re.compile(r"(最判|最高裁|判決|事件)")
MATERIAL_HINT = re.compile(r"資料")

_SIDE_HINTS: Tuple[Tuple[re.Pattern, Side], ...] = (
    (re.compile(r"廃止賛成|賛成側|するべきである"), Side.PRO),
    (re.compile(r"廃止反対|反対側|するべきでない|すべきでない"), Side.CON),
)


def detect_side(text: str) -> Optional[Side]:
    """本文の冒頭から立場（賛成/反対）を推定する。"""
    head = "".join(text.splitlines()[:12])
    for pattern, side in _SIDE_HINTS:
        if pattern.search(head):
            return side
    return None


def extract_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return "無題の立論"


def classify_citation(label: str) -> CitationKind:
    if MATERIAL_HINT.search(label):
        return CitationKind.MATERIAL
    if CASE_HINT.search(label):
        return CitationKind.CASE
    if STATUTE_HINT.search(label):
        return CitationKind.STATUTE
    return CitationKind.OTHER


def extract_citations(text: str) -> List[Citation]:
    citations: List[Citation] = []
    seen: set[str] = set()
    for match in CITATION.finditer(text):
        for part in re.split(r"[、,]\s*", match.group(1)):
            label = part.replace("参照", "").strip()
            if not label or label in seen:
                continue
            seen.add(label)
            citations.append(
                raw_citation(match.group(0), label),
            )
    return citations


def raw_citation(raw: str, label: str) -> Citation:
    return Citation(raw=raw, label=label, kind=classify_citation(label))


def extract_claim(text: str) -> str:
    """論証ブロックの結論にあたる一文を取り出す。"""
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    if not sentences:
        return ""
    for sentence in reversed(sentences):
        if any(marker in sentence for marker in CLAIM_MARKERS):
            return CITATION.sub("", sentence).strip()
    return CITATION.sub("", sentences[-1]).strip()


def _match_heading(line: str) -> Optional[Tuple[int, str, str]]:
    """行が見出しであれば (階層, 番号, 見出し文) を返す。"""
    roman = ROMAN_HEADING.match(line)
    if roman:
        return 0, roman.group(1), roman.group(2).strip()
    number = NUMBER_HEADING.match(line)
    if number:
        return 1, number.group(1), number.group(2).strip()
    paren = PAREN_HEADING.match(line)
    if paren:
        return 2, f"({paren.group(1)})", paren.group(2).strip()
    return None


def parse_document(
    document_id: str, side: Side, text: str
) -> List[Argument]:
    """立論本文を論証ブロックへ分解する。"""
    numbering: List[str] = ["", "", ""]
    blocks: List[dict] = []
    current: Optional[dict] = None

    for raw_line in text.splitlines():
        line = raw_line.strip().replace("\u3000", " ").strip()
        if not line:
            continue
        heading = _match_heading(line)
        if heading is None:
            if current is not None:
                current["body"].append(line)
            continue

        level, number, title = heading
        numbering[level] = number
        for deeper in range(level + 1, 3):
            numbering[deeper] = ""
        section = ".".join(part for part in numbering if part)
        current = {
            "section": section,
            "heading": title or "（見出しなし）",
            "body": [title] if len(title) > 25 else [],
        }
        blocks.append(current)

    arguments: List[Argument] = []
    for index, block in enumerate(blocks, start=1):
        body = "".join(block["body"])
        if len(body) < MIN_BLOCK_LENGTH:
            continue
        citations = extract_citations(body)
        warnings: List[str] = []
        if not citations and len(body) >= UNSUPPORTED_MIN_LENGTH:
            warnings.append("出典（【】表記）が一つも示されていません")
        if len(body) > 600:
            warnings.append("1ブロックが長すぎます（600字超）。争点ごとの分割を検討してください")
        arguments.append(
            Argument(
                id=f"{document_id}-a{index}",
                side=side,
                document_id=document_id,
                section=block["section"],
                heading=block["heading"],
                text=body,
                claim=extract_claim(body),
                citations=citations,
                warnings=warnings,
            )
        )
    return arguments
