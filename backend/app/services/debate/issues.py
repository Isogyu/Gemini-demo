"""争点辞書と、論証ブロックを争点へ割り当てるロジック。

租税法のディベートで頻出する評価軸（担税力・公平・中立・簡素・立法事実・比較衡量）を
キーワード重み付けで判定し、賛否を突き合わせた論点マップ（IssueClash）を組み立てる。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from app.schemas.debate import (
    Argument,
    ClashStatus,
    IssueClash,
    IssueStance,
    Side,
)


@dataclass(frozen=True)
class IssueDefinition:
    id: str
    label: str
    description: str
    keywords: Dict[str, float] = field(default_factory=dict)


ISSUE_DEFINITIONS: Sequence[IssueDefinition] = (
    IssueDefinition(
        id="ability_to_pay",
        label="担税力に即した課税",
        description="必要経費控除と担税力の関係。所得を構成しない投下資本の回収部分への課税の当否。",
        keywords={
            "担税力": 3.0,
            "純資産増加説": 3.0,
            "必要経費": 2.0,
            "投下資本": 2.0,
            "控除": 1.0,
            "家事費": 1.5,
        },
    ),
    IssueDefinition(
        id="equity",
        label="公平（比較対象の設定）",
        description="「同様の状況」をどう切り出すか。区別の目的と手段の合理性。",
        keywords={
            "公平": 3.0,
            "平等": 2.0,
            "同様の状況": 3.0,
            "区別": 2.0,
            "所得分散": 1.5,
            "14条": 2.0,
            "一律": 1.0,
        },
    ),
    IssueDefinition(
        id="neutrality",
        label="中立（経済的選択の歪み）",
        description="税制が事業形態・就労形態の選択を歪めるか否か。",
        keywords={
            "中立": 3.0,
            "歪": 2.0,
            "法人成り": 2.5,
            "無償労働": 2.5,
            "選択": 1.0,
            "偏り": 1.5,
            "偏向": 1.5,
        },
    ),
    IssueDefinition(
        id="simplicity",
        label="簡素・執行コスト",
        description="個別認定の回避による事務負担の軽減と、廃止後の徴税コスト。",
        keywords={
            "簡素": 3.0,
            "事務負担": 2.5,
            "徴税コスト": 2.5,
            "調査": 1.5,
            "執行": 1.5,
            "省略": 1.5,
            "包括": 1.5,
        },
    ),
    IssueDefinition(
        id="legislative_facts",
        label="立法事実の変化",
        description="制定当時の前提（家父長制・記帳慣行の未成熟）が現在も妥当するか。",
        keywords={
            "立法事実": 3.0,
            "家父長": 2.5,
            "記帳": 2.0,
            "多様化": 2.0,
            "共働き": 2.5,
            "専従者": 1.5,
            "時代遅れ": 2.5,
            "DX": 2.0,
            "普及": 1.0,
        },
    ),
    IssueDefinition(
        id="balancing",
        label="比較衡量・結論",
        description="規定の利点と廃止による利益の衡量。",
        keywords={
            "比較衡量": 3.0,
            "衡量": 2.0,
            "限定的": 1.5,
            "不利益": 1.5,
            "結論": 1.0,
        },
    ),
)

ISSUE_BY_ID: Dict[str, IssueDefinition] = {d.id: d for d in ISSUE_DEFINITIONS}

MIN_SCORE = 3.0
RELATIVE_THRESHOLD = 0.6


def score_issues(text: str) -> Dict[str, float]:
    """テキストに対する各争点のスコアを返す。"""
    scores: Dict[str, float] = {}
    for definition in ISSUE_DEFINITIONS:
        score = sum(
            weight * text.count(keyword)
            for keyword, weight in definition.keywords.items()
        )
        if score > 0:
            scores[definition.id] = score
    return scores


def assign_issues(argument: Argument) -> List[str]:
    """論証ブロックに争点 ID を割り当てる（見出しは本文より重く見る）。"""
    scores = score_issues(argument.text)
    for issue_id, heading_score in score_issues(argument.heading).items():
        scores[issue_id] = scores.get(issue_id, 0.0) + heading_score * 2.0
    if not scores:
        return []
    top = max(scores.values())
    if top < MIN_SCORE:
        return []
    return [
        issue_id
        for issue_id, score in sorted(scores.items(), key=lambda kv: -kv[1])
        if score >= max(MIN_SCORE, top * RELATIVE_THRESHOLD)
    ]


def _stance(side: Side, arguments: List[Argument]) -> Optional[IssueStance]:
    if not arguments:
        return None
    return IssueStance(
        side=side,
        argument_ids=[a.id for a in arguments],
        points=[a.claim for a in arguments if a.claim],
        citation_count=sum(len(a.citations) for a in arguments),
    )


def _status(pro: Optional[IssueStance], con: Optional[IssueStance]) -> ClashStatus:
    if pro and con:
        return ClashStatus.CLASH
    if pro:
        return ClashStatus.PRO_ONLY
    if con:
        return ClashStatus.CON_ONLY
    return ClashStatus.ABSENT


_NOTES = {
    ClashStatus.CLASH: "両者が同じ争点で正面から衝突しています。",
    ClashStatus.PRO_ONLY: "反対側がこの争点に応答していません（賛成側が無風で通す可能性があります）。",
    ClashStatus.CON_ONLY: "賛成側がこの争点に応答していません（反対側が無風で通す可能性があります）。",
    ClashStatus.ABSENT: "いずれの立論もこの争点に触れていません。",
}


def build_issue_map(arguments: List[Argument]) -> List[IssueClash]:
    """争点ごとに賛否を対置した論点マップを構築する。"""
    clashes: List[IssueClash] = []
    for definition in ISSUE_DEFINITIONS:
        pro_args = [
            a for a in arguments if a.side is Side.PRO and definition.id in a.issue_ids
        ]
        con_args = [
            a for a in arguments if a.side is Side.CON and definition.id in a.issue_ids
        ]
        pro = _stance(Side.PRO, pro_args)
        con = _stance(Side.CON, con_args)
        status = _status(pro, con)
        if status is ClashStatus.ABSENT:
            continue
        clashes.append(
            IssueClash(
                issue_id=definition.id,
                label=definition.label,
                description=definition.description,
                status=status,
                pro=pro,
                con=con,
                note=_NOTES[status],
            )
        )
    return clashes
