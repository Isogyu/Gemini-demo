from app.schemas.debate import CitationKind, Side
from app.services.debate.parser import (
    classify_citation,
    detect_side,
    extract_claim,
    extract_citations,
    parse_document,
)

SAMPLE = """廃止賛成側立論
Ⅰ. 主張
所得税法56条および57条を廃止するべきである。
Ⅱ. 理由
1. 問題点
（1）担税力に即した課税
純資産増加説を採用するわが国では必要経費を控除することとしている【法37条1項、資料2参照】。
しかし56条は親族への対価を一律に必要経費から除外しており、担税力に即した課税に反するといえる【資料3参照】。
（2）公平
公平とは同様の状況にあるものは同様に取り扱うことを要求する。
"""


def test_detect_side():
    assert detect_side(SAMPLE) is Side.PRO
    assert detect_side("廃止反対側立論\nⅠ. 主張\n廃止するべきでない。") is Side.CON
    assert detect_side("無関係な文章です。") is None


def test_parse_document_builds_hierarchical_sections():
    arguments = parse_document("doc1", Side.PRO, SAMPLE)
    sections = [a.section for a in arguments]
    assert sections == ["Ⅰ", "Ⅱ.1.(1)", "Ⅱ.1.(2)"]
    assert arguments[1].heading == "担税力に即した課税"


def test_parse_document_skips_headings_without_body():
    arguments = parse_document("doc1", Side.PRO, SAMPLE)
    assert all(a.section != "Ⅱ" for a in arguments)


def test_extract_citations_splits_and_classifies():
    citations = extract_citations("……である【法37条1項、資料2参照】。")
    assert [c.label for c in citations] == ["法37条1項", "資料2"]
    assert [c.kind for c in citations] == [CitationKind.STATUTE, CitationKind.MATERIAL]


def test_classify_citation():
    assert classify_citation("資料10") is CitationKind.MATERIAL
    assert classify_citation("最判平成16年11月2日") is CitationKind.CASE
    assert classify_citation("日本国憲法14条1項") is CitationKind.STATUTE
    assert classify_citation("インタビュー") is CitationKind.OTHER


def test_extract_claim_prefers_concluding_sentence():
    text = "前提となる説明である。したがって公平性に反するといえる【資料4参照】。"
    assert extract_claim(text) == "したがって公平性に反するといえる。"


def test_argument_without_citation_is_flagged():
    arguments = parse_document("doc1", Side.PRO, SAMPLE)
    warned = [a for a in arguments if a.warnings]
    assert any("出典" in w for a in warned for w in a.warnings)
