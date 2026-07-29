import pytest

from app.schemas.debate import (
    ClashStatus,
    DebateAnalysisRequest,
    DebateDocumentInput,
    RebuttalStrength,
    Side,
)
from app.services.debate.analysis import analyze
from app.services.debate.issues import assign_issues, score_issues
from app.services.debate.parser import parse_document
from app.services.debate.samples import get_debate_sample


@pytest.fixture(scope="module")
def analysis():
    sample = get_debate_sample("income-tax-56-57")
    return analyze(
        DebateAnalysisRequest(documents=sample.documents, topic=sample.topic)
    )


def _issue(analysis, issue_id):
    return next(i for i in analysis.issues if i.issue_id == issue_id)


def test_score_issues_weights_keywords():
    scores = score_issues("担税力に即した課税と必要経費の控除")
    assert scores["ability_to_pay"] > scores.get("equity", 0)


def test_assign_issues_uses_heading_weight():
    arguments = parse_document(
        "doc1", Side.CON, "（3）簡素\n事例ごとの判断や複雑な調査を省略している。"
    )
    assert assign_issues(arguments[0]) == ["simplicity"]


def test_clash_detected_on_shared_issues(analysis):
    assert _issue(analysis, "equity").status is ClashStatus.CLASH
    assert _issue(analysis, "neutrality").status is ClashStatus.CLASH


def test_unanswered_issues_are_reported(analysis):
    assert _issue(analysis, "ability_to_pay").status is ClashStatus.PRO_ONLY
    assert _issue(analysis, "simplicity").status is ClashStatus.CON_ONLY


def test_gap_rebuttal_targets_the_silent_side(analysis):
    gaps = {
        (r.issue_id, r.target_side)
        for r in analysis.rebuttals
        if r.pattern_id == "clash_gap"
    }
    assert ("ability_to_pay", Side.CON) in gaps
    assert ("simplicity", Side.PRO) in gaps


def test_rebuttals_carry_trigger_text(analysis):
    over_inclusive = next(
        r for r in analysis.rebuttals if r.pattern_id == "over_inclusive"
    )
    assert over_inclusive.target_side is Side.CON
    assert "予め防止" in over_inclusive.trigger
    assert over_inclusive.cross_examination


def test_rebuttals_sorted_by_strength(analysis):
    strengths = [r.strength for r in analysis.rebuttals]
    assert strengths[0] is RebuttalStrength.HIGH
    assert strengths[-1] is RebuttalStrength.LOW


def test_evidence_report_collects_sources(analysis):
    pro = next(e for e in analysis.evidence if e.side is Side.PRO)
    assert "日本国憲法14条1項" in pro.statutes
    assert "資料10" in pro.materials


def test_analyze_rejects_text_without_headings():
    with pytest.raises(ValueError):
        analyze(
            DebateAnalysisRequest(
                documents=[
                    DebateDocumentInput(side=Side.PRO, text="見出しのない普通の文章です。")
                ]
            )
        )


def test_analyze_accepts_single_document():
    sample = get_debate_sample("income-tax-56-57")
    result = analyze(DebateAnalysisRequest(documents=[sample.documents[0]]))
    assert all(i.status is not ClashStatus.CLASH for i in result.issues)
