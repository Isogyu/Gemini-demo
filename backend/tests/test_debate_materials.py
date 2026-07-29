from app.schemas.debate import (
    DebateAnalysisRequest,
    MaterialLinkStatus,
    ReferenceDocumentInput,
    Side,
    StatuteConsistencyStatus,
)
from app.schemas.statute import StatuteArticle, StatuteLookupStatus
from app.services.debate.analysis import analyze, attach_statutes
from app.services.debate.materials import (
    build_reference_check,
    parse_reference_packet,
)
from app.services.debate.parser import parse_document

PACKET_TEXT = """廃止賛成側参考資料
Ⅰ. 関連法令
1. 日本国憲法
第14条1項　すべて国民は、法の下に平等であつて、差別されない。
2. 所得税法
第56条　居住者と生計を一にする配偶者その他の親族が対価の支払を受ける場合には、必要経費に算入しない。
第57条1項　青色事業専従者が給与の支払を受けた場合には、必要経費に算入する。
２項　青色事業専従者の氏名を記載した書類を提出しなければならない。
Ⅱ. 資料
1. 租税公平主義
「税負担は担税力に即して公平に配分されなければならない。」
金子宏『租税法〔第24版〕』（弘文堂・2021年）88頁
2. 必要経費とは
佐藤英明『スタンダード所得税法〔第4版〕』（弘文堂・2024年）279頁
3. 出典のない資料
"""

ARGUMENT_TEXT = """廃止賛成側立論
Ⅰ. 主張
所得税法56条を廃止するべきである。
1. 租税公平主義
租税公平主義は担税力に即した公平な配分を要請している【資料1参照】。したがって56条は租税公平主義に反するといえる。
2. 必要経費
必要経費の控除は投下資本の回収部分を課税から除くためのものである【法37条1項、資料2参照】。56条はこれを一律に否定するため、担税力に即した課税に反するといえる。
3. 存在しない資料の引用
56条の立法事実は失われている【資料9参照】。したがって廃止すべきである。
"""


def _packet() -> ReferenceDocumentInput:
    return ReferenceDocumentInput(side=Side.PRO, title="", text=PACKET_TEXT)


def test_parse_reference_packet_splits_statutes_and_materials():
    packet = parse_reference_packet(_packet())
    assert packet.title == "廃止賛成側参考資料"
    assert [s.label for s in packet.statutes] == [
        "日本国憲法第14条第1項",
        "所得税法第56条",
        "所得税法第57条第1項",
        "所得税法第57条第2項",
    ]
    assert [m.number for m in packet.materials] == [1, 2, 3]
    assert packet.materials[0].label == "租税公平主義"
    assert packet.materials[0].sources == ["金子宏『租税法〔第24版〕』（弘文堂・2021年）88頁"]
    assert "担税力に即して" in packet.materials[0].excerpt
    assert packet.materials[2].sources == []


def test_build_reference_check_detects_missing_and_unused_materials():
    arguments = parse_document("doc1-pro", Side.PRO, ARGUMENT_TEXT)
    check = build_reference_check(parse_reference_packet(_packet()), arguments)
    by_number = {link.number: link for link in check.material_links}

    assert by_number[1].status == MaterialLinkStatus.LINKED
    assert by_number[1].cited_by
    assert by_number[3].status == MaterialLinkStatus.UNUSED
    assert by_number[9].status == MaterialLinkStatus.MISSING
    assert check.missing_numbers == [9]
    assert check.unused_numbers == [3]
    assert by_number[2].note == ""
    assert "出典文献" in by_number[3].note or by_number[3].note


def test_statute_consistency_compares_with_current_text():
    packet = parse_reference_packet(_packet())
    current = {
        "所得税法第56条": "居住者と生計を一にする配偶者その他の親族が対価の支払を受ける場合には、必要経費に算入しない。",
        "日本国憲法第14条第1項": "すべて国民は、法の下に平等であつて、人種、信条により差別されない。",
    }
    check = build_reference_check(packet, [], current)
    by_label = {c.label: c for c in check.statute_consistency}

    assert by_label["所得税法第56条"].status == StatuteConsistencyStatus.CONSISTENT
    assert by_label["日本国憲法第14条第1項"].status == StatuteConsistencyStatus.DIFFERS
    assert by_label["所得税法第57条第1項"].status == StatuteConsistencyStatus.UNVERIFIED


def test_analyze_collects_statute_references_from_arguments_and_packet():
    request = DebateAnalysisRequest(
        documents=[{"side": "pro", "text": ARGUMENT_TEXT}],
        references=[_packet()],
        topic="所得税法56条の廃止",
    )
    analysis = analyze(request)
    labels = [r.label for r in analysis.statute_references]

    assert "所得税法第56条" in labels
    assert "所得税法第37条第1項" in labels
    assert "日本国憲法第14条" in labels, "参考資料の関連法令も取得対象に含める"
    assert analysis.reference_checks[0].missing_numbers == [9]


def test_attach_statutes_recomputes_consistency():
    request = DebateAnalysisRequest(
        documents=[{"side": "pro", "text": ARGUMENT_TEXT}],
        references=[_packet()],
    )
    analysis = analyze(request)
    attach_statutes(
        analysis,
        request,
        [
            StatuteArticle(
                label="所得税法第56条",
                law_name="所得税法",
                article=56,
                text="居住者と生計を一にする配偶者その他の親族が対価の支払を受ける場合には、必要経費に算入しない。",
                status=StatuteLookupStatus.FOUND,
            )
        ],
    )
    statuses = {
        c.label: c.status for c in analysis.reference_checks[0].statute_consistency
    }
    assert statuses["所得税法第56条"] == StatuteConsistencyStatus.CONSISTENT
