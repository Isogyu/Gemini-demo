"""反駁候補と想定尋問の生成。

「相手の立論のどの文言が、どの反駁の型（pattern）を呼び込むか」を明示した
カタログを引き当てる方式にしている。生成物には必ず起点となった文言（trigger）が
付くため、資料に無い主張を作り出さない。
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from app.schemas.debate import (
    Argument,
    ClashStatus,
    IssueClash,
    Rebuttal,
    RebuttalStrength,
    Side,
)
from app.services.debate.issues import ISSUE_BY_ID

_OPPONENT: Dict[Side, Side] = {Side.PRO: Side.CON, Side.CON: Side.PRO}
_SIDE_LABEL: Dict[Side, str] = {Side.PRO: "賛成（廃止）側", Side.CON: "反対（存続）側"}


@dataclass(frozen=True)
class RebuttalPattern:
    """反駁の型。target_side の立論に trigger が現れたときに発火する。"""

    id: str
    title: str
    target_side: Side
    issue_ids: Tuple[str, ...]
    trigger: str
    body: str
    cross_examination: Tuple[str, ...]
    strength: RebuttalStrength
    absent_in_target: Optional[str] = field(
        default=None,
        metadata={"doc": "相手の立論全体にこの語がない場合にのみ発火する"},
    )


PATTERNS: Sequence[RebuttalPattern] = (
    RebuttalPattern(
        id="over_inclusive",
        title="過剰包摂 — 目的に照らした比較対象がずれている",
        target_side=Side.CON,
        issue_ids=("equity", "neutrality"),
        trigger=r"一律|包括的|予め防止|一切",
        body=(
            "相手は「親族への支払 vs 第三者への支払」を比較しているが、規制目的は"
            "「恣意的な所得分散の防止」である。目的に照らした正しい比較対象は"
            "「分散をしていない親族間取引 vs 分散をした親族間取引」であり、前者まで"
            "否認する現行法は目的との関係で過剰包摂（over-inclusive）である。"
            "相手自身が区別の「目的」の合理性を論じている以上、手段は目的との関連で"
            "審査されなければならず、独立当事者間価格基準・記帳要件・上限額規制といった"
            "より制限的でない手段が存在する以上、手段の合理性は認められない。"
        ),
        cross_examination=(
            "56条等の目的が恣意的な所得分散の防止であることは争いませんね？",
            "では、分散を行っていない納税者にまで否認が及ぶことは、その目的の達成に必要ですか？",
            "上限額規制や書面要件では目的を達成できない理由は何ですか？",
        ),
        strength=RebuttalStrength.HIGH,
    ),
    RebuttalPattern(
        id="alternative_means",
        title="代替手段の存在 — 56条は屋上屋",
        target_side=Side.CON,
        issue_ids=("equity", "neutrality", "simplicity"),
        trigger=r"所得分散|租税回避|脱税",
        body=(
            "所得分散への対処手段は既に別に用意されている。過大な対価は必要経費の"
            "相当性（法37条1項）で否認でき、同族関係を利用した不自然な取引は法157条で"
            "対応できる。法人成りした場合も過大役員給与の損金不算入規制が働く。"
            "56条がなくとも所得分散は防止できる以上、同条を維持する必要性は失われている。"
        ),
        cross_examination=(
            "過大な対価の支払は、37条1項の必要経費の相当性では否認できませんか？",
            "56条を残さなければ防げない所得分散の具体例を挙げられますか？",
        ),
        strength=RebuttalStrength.HIGH,
    ),
    RebuttalPattern(
        id="simplicity_not_achieved",
        title="「簡素」は既に達成されていない",
        target_side=Side.CON,
        issue_ids=("simplicity",),
        trigger=r"簡素|省略|包括",
        body=(
            "57条は「専ら従事」要件と「労務の対価として相当」であることの個別認定を"
            "要求しており、包括処理という前提が既に崩れている。加えて56条の"
            "「その他の事由」の解釈をめぐって最高裁まで争われた事実（弁護士夫婦事件・"
            "最判平成16年11月2日等）は、この規定が簡素どころか新たな紛争コストを"
            "生んでいることの証左である。"
        ),
        cross_examination=(
            "57条の「労務の対価として相当」かどうかは、誰がどのように判断していますか？",
            "それは「個別の判断を省略できる」という主張と両立しますか？",
        ),
        strength=RebuttalStrength.HIGH,
    ),
    RebuttalPattern(
        id="statistics_endogeneity",
        title="統計の因果の向き（内生性）",
        target_side=Side.CON,
        issue_ids=("legislative_facts", "balancing"),
        trigger=r"[0-9０-９]+(?:\.[0-9]+)?[%％]|割合|減少",
        body=(
            "示された減少傾向は、56条等による不利益が事業者に法人成りや親族の無償労働を"
            "選ばせた結果とも読める。因果の向きが特定されていない以上、この統計は"
            "むしろ「中立性が侵害されている」ことの証拠に転化しうる。加えて"
            "「対象者が少ないから救済は不要」という論法は、平等原則の議論としては成立しない。"
        ),
        cross_examination=(
            "専従者の割合が減少した原因が56条等による不利益にある可能性を否定できますか？",
            "対象となる納税者が少数であることは、平等取扱いを否定する理由になりますか？",
        ),
        strength=RebuttalStrength.MEDIUM,
    ),
    RebuttalPattern(
        id="population_mismatch",
        title="名宛人集団のずれ — 統計が論点をすり替えている",
        target_side=Side.CON,
        issue_ids=("legislative_facts", "balancing"),
        trigger=r"共働き|雇用者",
        body=(
            "引用されている統計は雇用者世帯の話であり、56条等の名宛人は事業所得者である。"
            "名宛人集団の外側の統計によって、名宛人に対する規制の合理性を基礎づけることはできない。"
        ),
        cross_examination=(
            "共働き世帯の増加は、事業所得者に対する規制の合理性とどう結び付きますか？",
        ),
        strength=RebuttalStrength.MEDIUM,
    ),
    RebuttalPattern(
        id="household_transfer",
        title="経費性の立証可能性を素通りしている",
        target_side=Side.PRO,
        issue_ids=("ability_to_pay",),
        trigger=r"担税力|必要経費|投下資本",
        body=(
            "生計を一にする親族間では家計と事業の資金が混在しており、対価の支払は実質的に"
            "世帯内の資金移転にすぎない場合が多い。相手の主張は「経費性が立証できる場合」を"
            "暗黙の前提としており、立証困難という前提事実そのものを争っていない。"
        ),
        cross_examination=(
            "親族間の役務提供について、対価が相当であることを税務署はどう確認できますか？",
            "家事費と必要経費が混在している場合、どちらの負担で区分しますか？",
        ),
        strength=RebuttalStrength.HIGH,
    ),
    RebuttalPattern(
        id="inference_gap_dx",
        title="論証の飛躍 — DX・記帳義務化から執行可能性への架橋がない",
        target_side=Side.PRO,
        issue_ids=("legislative_facts",),
        trigger=r"DX|記帳|効率化|高度化",
        body=(
            "記帳義務の存在は記帳内容の真実性を保証しない。親族間の役務提供の有無と"
            "相当額の認定は本質的に情報の非対称性の問題であり、電子化では解決しない。"
            "相手は「DXが推進されている」という事実は示しているが、「だから相当性を"
            "認定できる」という架橋の論証を欠いている。"
        ),
        cross_examination=(
            "税務行政のDXによって、親族間の役務提供の実態が確認できるようになる仕組みを説明できますか？",
            "記帳義務があれば記帳内容が真実であることは担保されますか？",
        ),
        strength=RebuttalStrength.MEDIUM,
    ),
    RebuttalPattern(
        id="burden_of_proof",
        title="「政府が検討中」は廃止の根拠にならない",
        target_side=Side.PRO,
        issue_ids=("legislative_facts", "balancing"),
        trigger=r"検討|政府|2009",
        body=(
            "政府が結論を出していないことは、廃止すべきという合意が形成されていないことの"
            "証左であって、放置の証拠ではない。立法事実が変化したことの立証責任は"
            "現状変更を求める側にある。"
        ),
        cross_examination=(
            "政府が結論を出していないことは、なぜ廃止すべきことの根拠になるのですか？",
        ),
        strength=RebuttalStrength.LOW,
    ),
    RebuttalPattern(
        id="no_alternative_design",
        title="代替案なき廃止論 — 廃止後の制度設計が示されていない",
        target_side=Side.PRO,
        issue_ids=("balancing", "simplicity", "legislative_facts"),
        trigger=r"廃止",
        body=(
            "廃止後に必要となる個別認定の執行コストの見積りも、代替する制度設計"
            "（相当額の判定基準・書面要件など）も示されていない。制度の撤廃だけを"
            "主張し、撤廃後の秩序を示さない議論は、比較衡量の一方の皿が空である。"
        ),
        cross_examination=(
            "廃止した場合の追加的な執行コストを試算していますか？",
            "廃止後、対価の相当性はどの規定で判定しますか？",
        ),
        strength=RebuttalStrength.MEDIUM,
        absent_in_target=r"代替|上限額|相当額の基準|独立当事者間",
    ),
)


def _issue_label(issue_id: str) -> str:
    definition = ISSUE_BY_ID.get(issue_id)
    return definition.label if definition else issue_id


def _find_trigger(pattern: RebuttalPattern, argument: Argument) -> Optional[str]:
    match = re.search(pattern.trigger, argument.text)
    if match is None:
        return None
    start = max(0, match.start() - 20)
    end = min(len(argument.text), match.end() + 20)
    return f"…{argument.text[start:end]}…"


def _gap_rebuttal(clash: IssueClash, index: int) -> Rebuttal:
    silent_side = Side.CON if clash.status is ClashStatus.PRO_ONLY else Side.PRO
    speaking_side = _OPPONENT[silent_side]
    return Rebuttal(
        id=f"gap-{index}",
        pattern_id="clash_gap",
        target_side=silent_side,
        issue_id=clash.issue_id,
        issue_label=clash.label,
        title=f"無応答の争点 — 「{clash.label}」に反論がない",
        body=(
            f"{_SIDE_LABEL[speaking_side]}がこの争点を提起しているのに対し、"
            f"{_SIDE_LABEL[silent_side]}は正面から応答していない。"
            "無応答の争点は相手の主張が事実上通ったものとして扱われるため、"
            "ここを指摘したうえで、自陣の評価軸の中でこの争点をどう位置づけるかを述べるべきである。"
        ),
        trigger="（相手立論に対応する記述なし）",
        cross_examination=[
            f"「{clash.label}」について、あなた方の立論のどこで応答していますか？",
        ],
        strength=RebuttalStrength.HIGH,
    )


def _unsupported_rebuttal(argument: Argument, index: int) -> Rebuttal:
    issue_id = argument.issue_ids[0] if argument.issue_ids else "balancing"
    return Rebuttal(
        id=f"unsupported-{index}",
        pattern_id="unsupported_claim",
        target_side=argument.side,
        issue_id=issue_id,
        issue_label=_issue_label(issue_id),
        title=f"出典のない主張 — {argument.section} {argument.heading}",
        body=(
            "この論証ブロックには出典（【】表記）が一つも付されていない。"
            "資料の裏付けがない主張は、そのまま争えば「根拠なき断定」として処理できる。"
        ),
        trigger=argument.claim or argument.text[:60],
        cross_examination=[
            "その主張の出典を示してください。資料のどこに書かれていますか？",
        ],
        strength=RebuttalStrength.MEDIUM,
    )


def generate_rebuttals(
    arguments: List[Argument], issues: List[IssueClash]
) -> List[Rebuttal]:
    """論点マップと立論本文から反駁候補を生成する。"""
    rebuttals: List[Rebuttal] = []

    for index, clash in enumerate(issues, start=1):
        if clash.status in (ClashStatus.PRO_ONLY, ClashStatus.CON_ONLY):
            rebuttals.append(_gap_rebuttal(clash, index))

    side_text = {
        side: "".join(a.text for a in arguments if a.side is side)
        for side in (Side.PRO, Side.CON)
    }

    used: set[str] = set()
    for pattern in PATTERNS:
        if pattern.absent_in_target and re.search(
            pattern.absent_in_target, side_text[pattern.target_side]
        ):
            continue
        for argument in arguments:
            if argument.side is not pattern.target_side:
                continue
            if pattern.issue_ids and not set(pattern.issue_ids) & set(argument.issue_ids):
                continue
            trigger = _find_trigger(pattern, argument)
            if trigger is None or pattern.id in used:
                continue
            used.add(pattern.id)
            issue_id = next(
                (i for i in pattern.issue_ids if i in argument.issue_ids),
                argument.issue_ids[0] if argument.issue_ids else pattern.issue_ids[0],
            )
            rebuttals.append(
                Rebuttal(
                    id=f"{pattern.id}",
                    pattern_id=pattern.id,
                    target_side=pattern.target_side,
                    issue_id=issue_id,
                    issue_label=_issue_label(issue_id),
                    title=pattern.title,
                    body=pattern.body,
                    trigger=trigger,
                    cross_examination=list(pattern.cross_examination),
                    strength=pattern.strength,
                )
            )

    for index, argument in enumerate(arguments, start=1):
        if not argument.citations and len(argument.text) >= 80:
            rebuttals.append(_unsupported_rebuttal(argument, index))

    order = {
        RebuttalStrength.HIGH: 0,
        RebuttalStrength.MEDIUM: 1,
        RebuttalStrength.LOW: 2,
    }
    rebuttals.sort(key=lambda r: (order[r.strength], r.target_side.value))
    return rebuttals
