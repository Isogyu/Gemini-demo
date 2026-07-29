"""テスト用のダミー e-Gov クライアント（ネットワークアクセスを行わない）。"""

from typing import Dict, List, Tuple

from app.services.statute.egov import (
    ArticleContent,
    EgovUnavailableError,
    LawInfo,
    LawNotFoundError,
)

LAW_NUMS: Dict[str, str] = {
    "所得税法": "昭和四十年法律第三十三号",
    "日本国憲法": "昭和二十一年憲法",
    "税制改革法": "昭和六十三年法律第百七号",
}

ARTICLES: Dict[Tuple[str, int], ArticleContent] = {
    ("昭和四十年法律第三十三号", 56): ArticleContent(
        caption="（事業から対価を受ける親族がある場合の必要経費の特例）",
        text="居住者と生計を一にする配偶者その他の親族が対価の支払を受ける場合には、必要経費に算入しない。",
        paragraph_texts=["居住者と生計を一にする配偶者その他の親族が対価の支払を受ける場合には、必要経費に算入しない。"],
    ),
    ("昭和四十年法律第三十三号", 57): ArticleContent(
        caption="（事業に専従する親族がある場合の必要経費の特例等）",
        text="青色事業専従者が給与の支払を受けた場合には、必要経費に算入する。",
        paragraph_texts=[
            "青色事業専従者が給与の支払を受けた場合には、必要経費に算入する。",
            "青色事業専従者の氏名を記載した書類を提出しなければならない。",
        ],
    ),
}


class FakeEgovClient:
    """固定の応答を返すクライアント。"""

    def __init__(self, unavailable: bool = False) -> None:
        self.unavailable = unavailable
        self.calls: List[str] = []

    def find_law(self, law_name: str) -> LawInfo:
        self.calls.append(f"find:{law_name}")
        if self.unavailable:
            raise EgovUnavailableError("e-Gov 法令API に接続できません")
        if law_name not in LAW_NUMS:
            raise LawNotFoundError(law_name)
        return LawInfo(law_name=law_name, law_num=LAW_NUMS[law_name], law_id="340")

    def fetch_article(self, law_num: str, article: int) -> ArticleContent:
        self.calls.append(f"article:{law_num}:{article}")
        if self.unavailable:
            raise EgovUnavailableError("e-Gov 法令API に接続できません")
        try:
            return ARTICLES[(law_num, article)]
        except KeyError as exc:
            raise LawNotFoundError(f"{law_num} 第{article}条") from exc
