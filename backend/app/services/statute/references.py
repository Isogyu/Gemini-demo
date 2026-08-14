"""立論本文から法令参照（法令名・条・項）を抽出する。

「所得税法56条」「法37条1項」「日本国憲法14条1項」「第五十六条」のような
日本の法律文書で慣用される表記を規則ベースで正規化する。
"""

import re
from typing import Dict, List, Optional

from app.schemas.statute import StatuteReference

DEFAULT_LAW_NAME = "所得税法"

#: 略称・文脈依存表記から正式名称へのマッピング。
LAW_ALIASES: Dict[str, str] = {
    "法": "",  # 文脈上の主たる法令（default_law_name）に解決する
    "同法": "",
    "本法": "",
    "所法": "所得税法",
    "憲法": "日本国憲法",
    "日本国憲法": "日本国憲法",
    "所得税法": "所得税法",
    "法人税法": "法人税法",
    "国税通則法": "国税通則法",
    "税制改革法": "税制改革法",
    "民法": "民法",
}

_ZEN_TO_HAN = str.maketrans("０１２３４５６７８９", "0123456789")
_KANJI_DIGITS = {
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_NUMBER_CHARS = "0-9０-９〇一二三四五六七八九十百"

LAW_NAME_PATTERN = "|".join(
    sorted((re.escape(name) for name in LAW_ALIASES), key=len, reverse=True)
)
REFERENCE = re.compile(
    rf"(?:(?P<law>{LAW_NAME_PATTERN})\s*)?"
    rf"第?(?P<article>[{_NUMBER_CHARS}]{{1,6}})条"
    rf"(?:\s*第?(?P<paragraph>[{_NUMBER_CHARS}]{{1,3}})項)?"
)


def parse_number(text: str) -> Optional[int]:
    """「56」「５６」「五十六」を整数へ変換する。"""
    normalized = text.translate(_ZEN_TO_HAN)
    if normalized.isdigit():
        return int(normalized)

    total = 0
    current = 0
    for char in normalized:
        if char in _KANJI_DIGITS:
            current = _KANJI_DIGITS[char]
        elif char == "十":
            total += (current or 1) * 10
            current = 0
        elif char == "百":
            total += (current or 1) * 100
            current = 0
        else:
            return None
    total += current
    return total or None


def normalize_law_name(raw: Optional[str], default_law_name: str) -> str:
    if not raw:
        return default_law_name
    resolved = LAW_ALIASES.get(raw, raw)
    return resolved or default_law_name


def build_label(law_name: str, article: int, paragraph: Optional[int]) -> str:
    label = f"{law_name}第{article}条"
    if paragraph:
        label += f"第{paragraph}項"
    return label


def extract_statute_references(
    text: str, default_law_name: str = DEFAULT_LAW_NAME
) -> List[StatuteReference]:
    """本文中の法令参照を抽出する（同一条項は最初の表記に統合）。"""
    references: List[StatuteReference] = []
    seen: Dict[str, StatuteReference] = {}
    for match in REFERENCE.finditer(text):
        article = parse_number(match.group("article"))
        if article is None:
            continue
        paragraph_raw = match.group("paragraph")
        paragraph = parse_number(paragraph_raw) if paragraph_raw else None
        law_name = normalize_law_name(match.group("law"), default_law_name)
        label = build_label(law_name, article, paragraph)
        if label in seen:
            continue
        reference = StatuteReference(
            raw=match.group(0).strip(),
            law_name=law_name,
            article=article,
            paragraph=paragraph,
            label=label,
        )
        seen[label] = reference
        references.append(reference)
    return references
