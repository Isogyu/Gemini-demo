"""e-Gov 法令API（https://laws.e-gov.go.jp/api）の薄いクライアント。

- 法令名 → 法令番号の解決は API v2 （/api/2/laws?law_title=...）
- 条文本文の取得は API v1 （/api/1/articles;lawNum=...;article=...）
  v2 の law_data は法令全文（所得税法では 16MB 超）を返すため、条単位で
  取得できる v1 を用いる。
"""

from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

import httpx

API_BASE_URL = "https://laws.e-gov.go.jp"
DEFAULT_TIMEOUT = 20.0


class EgovUnavailableError(RuntimeError):
    """API に到達できない、または想定外の応答が返った。"""


class LawNotFoundError(LookupError):
    """法令名または条番号が見つからない。"""


@dataclass(frozen=True)
class LawInfo:
    law_name: str
    law_num: str
    law_id: str


@dataclass(frozen=True)
class ArticleContent:
    caption: str
    text: str
    paragraph_texts: List[str]


def law_search_url(law_name: str) -> str:
    return f"{API_BASE_URL}/api/2/laws?law_title={law_name}&limit=20"


def article_api_url(law_num: str, article: int) -> str:
    return f"{API_BASE_URL}/api/1/articles;lawNum={law_num};article={article}"


def law_page_url(law_id: str, article: Optional[int] = None) -> str:
    if not law_id:
        return f"{API_BASE_URL}/search/"
    url = f"{API_BASE_URL}/law/{law_id}"
    if article:
        url += f"#Mp-At_{article}"
    return url


class EgovClient:
    """条文取得のための HTTP クライアント。"""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def _get(self, url: str) -> httpx.Response:
        try:
            response = httpx.get(
                url, timeout=self._timeout, follow_redirects=True
            )
        except httpx.HTTPError as exc:
            raise EgovUnavailableError(f"e-Gov 法令API に接続できません: {exc}") from exc
        if response.status_code >= 500:
            raise EgovUnavailableError(
                f"e-Gov 法令API がエラーを返しました（{response.status_code}）"
            )
        return response

    def find_law(self, law_name: str) -> LawInfo:
        """法令名（完全一致優先）から法令番号を解決する。"""
        response = self._get(law_search_url(law_name))
        if response.status_code == 404:
            raise LawNotFoundError(law_name)
        try:
            laws = response.json().get("laws", [])
        except ValueError as exc:
            raise EgovUnavailableError("法令一覧の応答を解釈できません") from exc

        candidates = []
        for entry in laws:
            revision = entry.get("revision_info") or {}
            info = entry.get("law_info") or {}
            title = revision.get("law_title") or ""
            law_num = info.get("law_num") or ""
            if not title or not law_num:
                continue
            candidates.append(
                LawInfo(
                    law_name=title,
                    law_num=law_num,
                    law_id=info.get("law_id") or "",
                )
            )
        for candidate in candidates:
            if candidate.law_name == law_name:
                return candidate
        if not candidates:
            raise LawNotFoundError(law_name)
        return min(candidates, key=lambda c: len(c.law_name))

    def fetch_article(self, law_num: str, article: int) -> ArticleContent:
        """条単位で条文を取得する。"""
        response = self._get(article_api_url(law_num, article))
        if response.status_code == 404:
            raise LawNotFoundError(f"{law_num} 第{article}条")
        try:
            root = ElementTree.fromstring(response.text)
        except ElementTree.ParseError as exc:
            raise EgovUnavailableError("条文の応答を解釈できません") from exc
        code = root.findtext("./Result/Code")
        if code not in (None, "0"):
            raise LawNotFoundError(root.findtext("./Result/Message") or "not found")
        return parse_article_xml(root, article)


def get_egov_client() -> EgovClient:
    """FastAPI 依存性（テストでは差し替える）。"""
    return EgovClient()


def parse_article_xml(root: ElementTree.Element, article: int) -> ArticleContent:
    """/api/1/articles の XML から条文テキストを組み立てる。"""
    element = root.find(".//LawContents/Article")
    if element is None:
        raise LawNotFoundError(f"第{article}条")
    caption = (element.findtext("ArticleCaption") or "").strip()
    paragraph_texts: List[str] = []
    for paragraph in element.findall("Paragraph"):
        paragraph_sentence = paragraph.find("ParagraphSentence")
        sentences = [
            (node.text or "").strip()
            for node in (
                paragraph_sentence.iter("Sentence")
                if paragraph_sentence is not None
                else []
            )
            if (node.text or "").strip()
        ]
        items: List[str] = []
        for item in paragraph.findall("Item"):
            title = (item.findtext("ItemTitle") or "").strip()
            item_sentences = [
                (node.text or "").strip()
                for node in item.iter("Sentence")
                if (node.text or "").strip()
            ]
            if item_sentences:
                items.append(f"{title}　{''.join(item_sentences)}".strip())
        body = "".join(sentences)
        if items:
            body = "\n".join([body, *items]).strip()
        if body:
            paragraph_texts.append(body)
    if not paragraph_texts:
        raise LawNotFoundError(f"第{article}条")
    return ArticleContent(
        caption=caption,
        text="\n".join(paragraph_texts),
        paragraph_texts=paragraph_texts,
    )
