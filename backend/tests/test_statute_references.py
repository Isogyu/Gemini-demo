from xml.etree import ElementTree

import pytest

from app.services.statute.egov import (
    EgovClient,
    LawNotFoundError,
    law_page_url,
    parse_article_xml,
)
from app.services.statute.references import (
    build_label,
    extract_statute_references,
    parse_number,
)

ARTICLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<DataRoot>
  <Result><Code>0</Code><Message/></Result>
  <ApplData>
    <LawNum>昭和四十年法律第三十三号</LawNum>
    <LawContents>
      <Article Num="57">
        <ArticleCaption>（事業に専従する親族がある場合の必要経費の特例等）</ArticleCaption>
        <ArticleTitle>第五十七条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphSentence><Sentence Num="1">青色事業専従者が給与の支払を受けた場合には、必要経費に算入する。</Sentence></ParagraphSentence>
        </Paragraph>
        <Paragraph Num="3">
          <ParagraphSentence><Sentence Num="1">事業専従者がある場合には、次に掲げる金額を必要経費とみなす。</Sentence></ParagraphSentence>
          <Item Num="1">
            <ItemTitle>一</ItemTitle>
            <ItemSentence><Sentence Num="1">配偶者である事業専従者　八十六万円</Sentence></ItemSentence>
          </Item>
        </Paragraph>
      </Article>
    </LawContents>
  </ApplData>
</DataRoot>
"""


def test_parse_number_handles_kanji_and_fullwidth():
    assert parse_number("56") == 56
    assert parse_number("５７") == 57
    assert parse_number("五十六") == 56
    assert parse_number("百十四") == 114
    assert parse_number("あ") is None


def test_extract_statute_references_normalizes_abbreviations():
    text = (
        "必要経費に算入する【法37条1項】。"
        "56条および57条は必要経費算入を制限する。"
        "これは日本国憲法14条1項に反する。"
        "税制改革法3条も参照。"
    )
    labels = [r.label for r in extract_statute_references(text)]
    assert labels == [
        "所得税法第37条第1項",
        "所得税法第56条",
        "所得税法第57条",
        "日本国憲法第14条第1項",
        "税制改革法第3条",
    ]


def test_extract_statute_references_respects_default_law_name():
    references = extract_statute_references("法22条2項", default_law_name="法人税法")
    assert references[0].label == "法人税法第22条第2項"


def test_extract_statute_references_deduplicates():
    references = extract_statute_references("所得税法56条は……。56条は……。")
    assert [r.label for r in references] == ["所得税法第56条"]


def test_build_label():
    assert build_label("所得税法", 57, None) == "所得税法第57条"
    assert build_label("所得税法", 57, 3) == "所得税法第57条第3項"


def test_parse_article_xml_collects_paragraphs_and_items():
    content = parse_article_xml(ElementTree.fromstring(ARTICLE_XML), 57)
    assert content.caption == "（事業に専従する親族がある場合の必要経費の特例等）"
    assert len(content.paragraph_texts) == 2
    assert content.paragraph_texts[0].startswith("青色事業専従者")
    assert "八十六万円" in content.paragraph_texts[1]
    # 項本文が項内の号と重複して連結されないこと
    assert content.paragraph_texts[1].count("次に掲げる金額") == 1


def test_parse_article_xml_without_article_raises():
    with pytest.raises(LawNotFoundError):
        parse_article_xml(ElementTree.fromstring("<DataRoot/>"), 56)


def test_law_page_url():
    assert law_page_url("340AC0000000033", 56).endswith("340AC0000000033#Mp-At_56")
    assert law_page_url("") .endswith("/search/")


def test_find_law_prefers_exact_title(monkeypatch):
    client = EgovClient()

    class _Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "laws": [
                    {
                        "law_info": {"law_num": "昭和二十七年法律第百十一号", "law_id": "327"},
                        "revision_info": {"law_title": "所得税法等の臨時特例に関する法律"},
                    },
                    {
                        "law_info": {"law_num": "昭和四十年法律第三十三号", "law_id": "340"},
                        "revision_info": {"law_title": "所得税法"},
                    },
                ]
            }

    monkeypatch.setattr(client, "_get", lambda url: _Response())
    law = client.find_law("所得税法")
    assert law.law_num == "昭和四十年法律第三十三号"
    assert law.law_id == "340"
