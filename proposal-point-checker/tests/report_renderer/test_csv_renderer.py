import csv
import io
import pytest

from biddeer_checker.checklist_model.models import ChecklistItem
from biddeer_checker.document_parser.models import UserFacingLocator
from biddeer_checker.evidence_reasoning.models import (
    EvidenceStatus,
    JudgedEvidencePackage,
    ReasoningResult,
)
from biddeer_checker.evidence_retrieval.models import CandidateEvidence, EvidencePackage
from biddeer_checker.report_renderer.csv_renderer import CSVRenderer
from biddeer_checker.report_renderer.models import ChecklistReviewReport, ReportSummary


HEADERS = [
    "序号",
    "审核点名称",
    "审核要求",
    "检查结果",
    "结论说明",
    "证据位置",
    "证据摘录",
]


def _report(items):
    return ChecklistReviewReport(
        summary=ReportSummary(
            totalItems=len(items),
            statusCounts={},
            itemsRequiringManualReview=[],
        ),
        items=items,
    )


def _judged(item_id, status, reason="原因", basis="依据", prompt="复核提示"):
    return JudgedEvidencePackage(
        package=EvidencePackage(
            item=ChecklistItem(
                itemId=item_id,
                name=f"审核点 {item_id}",
                requirement=f"要求 {item_id}",
                note="",
            ),
            candidates=[],
        ),
        result=ReasoningResult(
            status=status,
            reason=reason,
            judgmentBasis=basis,
            manualCheckPrompt=prompt,
        ),
    )


def _rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))


def _candidate(
    source_doc="proposal.docx",
    exact_text="核心命中句",
    pre_context="前文",
    post_context="后文",
    heading_path=None,
    nearest_heading="项目经理说明",
    locator_hint="项目团队配置 > 项目经理说明",
    evidence_type="paragraph",
    row_index=None,
):
    return CandidateEvidence(
        blockIndex=3,
        userLocator=UserFacingLocator(
            sourceDocName=source_doc,
            headingPath=(
                ["项目团队配置", "项目经理说明"]
                if heading_path is None
                else heading_path
            ),
            nearestHeading=nearest_heading,
            nearbyText="附近文本",
            locatorHint=locator_hint,
            evidenceType=evidence_type,
        ),
        matchedKeywords=["项目经理"],
        exactText=exact_text,
        preContext=pre_context,
        postContext=post_context,
        nearbyImages=[],
        rowIndex=row_index,
    )


def test_csv_renderer_pdf_with_locator_hint():
    # 1. PDF evidence with locatorHint
    cand = _candidate(
        source_doc="text_layer_chinese.pdf",
        locator_hint="text_layer_chinese.pdf > 第 1 页"
    )
    j = _judged("ITEM-001", EvidenceStatus.CLEAR_EVIDENCE)
    j.package.candidates = [cand]

    rows = _rows(CSVRenderer.render(_report([j])))
    assert rows[1][5] == "text_layer_chinese.pdf > 第 1 页"


def test_csv_renderer_pdf_without_locator_hint():
    # 2. PDF evidence without locatorHint (should fall back cleanly)
    cand = _candidate(
        source_doc="text_layer_chinese.pdf",
        heading_path=["第一章节"],
        nearest_heading="第一部分",
        locator_hint=""
    )
    j = _judged("ITEM-001", EvidenceStatus.CLEAR_EVIDENCE)
    j.package.candidates = [cand]

    rows = _rows(CSVRenderer.render(_report([j])))
    assert rows[1][5] == "第一章节 / 第一部分"


def test_csv_renderer_docx_regression():
    # 3. DOCX regression: even if locatorHint contains PDF-like page info,
    # it must use the standard DOCX formatting structure.
    cand = _candidate(
        source_doc="proposal.docx",
        heading_path=["团队配置"],
        nearest_heading="项目经理",
        locator_hint="proposal.docx > 第 1 页"
    )
    j = _judged("ITEM-001", EvidenceStatus.CLEAR_EVIDENCE)
    j.package.candidates = [cand]

    rows = _rows(CSVRenderer.render(_report([j])))
    # Expected public repo formatting: "headings; hint"
    assert rows[1][5] == "团队配置 / 项目经理；proposal.docx > 第 1 页"


def test_csv_renderer_fixed_7_columns():
    # 4. CSV fixed 7 columns
    report = _report([
        _judged("ITEM-001", EvidenceStatus.CLEAR_EVIDENCE),
        _judged("ITEM-002", EvidenceStatus.SUSPECTED_EVIDENCE),
    ])
    rows = _rows(CSVRenderer.render(report))
    assert rows[0] == HEADERS
    assert len(rows[0]) == 7
    assert len(rows[1]) == 7
    assert len(rows[2]) == 7


def test_csv_renderer_no_adjudication_or_risk_terms():
    # 5. No pass/fail / 废标 / 风险等级 terms
    report = _report([
        _judged(status.value, status) for status in EvidenceStatus
    ])
    rendered = CSVRenderer.render(report)

    for forbidden in (
        "PASS",
        "FAIL",
        "RISK",
        "通过",
        "不通过",
        "合格",
        "不合格",
        "废标",
        "高风险",
        "低风险",
        "风险等级",
    ):
        assert forbidden not in rendered
