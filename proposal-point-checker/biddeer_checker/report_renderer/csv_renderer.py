import csv
import io
import re
from typing import Iterable

from biddeer_checker.evidence_reasoning.models import EvidenceStatus, ReasoningResult
from biddeer_checker.evidence_retrieval.models import CandidateEvidence
from biddeer_checker.report_renderer.models import ChecklistReviewReport


MAX_EXCERPT_LENGTH = 500

CSV_HEADERS = (
    "序号",
    "审核点名称",
    "审核要求",
    "检查结果",
    "结论说明",
    "证据位置",
    "证据摘录",
)

STATUS_LABELS = {
    EvidenceStatus.CLEAR_EVIDENCE: "已找到明确证据",
    EvidenceStatus.SUSPECTED_EVIDENCE: "疑似找到证据",
    EvidenceStatus.CONFLICTING_EVIDENCE: "发现冲突证据",
    EvidenceStatus.NOT_FOUND: "未找到证据",
    EvidenceStatus.INSUFFICIENT_EVIDENCE: "证据不足",
    EvidenceStatus.UNABLE_TO_JUDGE: "无法判断",
}


class CSVRenderer:
    @staticmethod
    def render(report: ChecklistReviewReport) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(
            output,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            lineterminator="\r\n",
        )
        writer.writerow(CSV_HEADERS)

        for display_index, judged in enumerate(report.items, start=1):
            item = judged.package.item
            candidate = judged.package.candidates[0] if judged.package.candidates else None
            writer.writerow(
                (
                    display_index,
                    item.name,
                    item.requirement,
                    STATUS_LABELS[judged.result.status],
                    CSVRenderer._build_conclusion(judged.result),
                    CSVRenderer._build_location(candidate),
                    CSVRenderer._build_excerpt(candidate),
                )
            )

        return output.getvalue()

    @staticmethod
    def _build_conclusion(result: ReasoningResult) -> str:
        return " ".join(
            CSVRenderer._unique_non_empty(
                (
                    result.reason,
                    result.judgmentBasis,
                    result.manualCheckPrompt,
                )
            )
        )

    @staticmethod
    def _unique_non_empty(values: Iterable[str | None]) -> list[str]:
        unique = []
        for value in values:
            normalized = CSVRenderer._normalize_text(value)
            if normalized and normalized not in unique:
                unique.append(normalized)
        return unique

    @staticmethod
    def _normalize_text(value: str | None) -> str:
        return " ".join((value or "").split())

    @staticmethod
    def _build_location(candidate: CandidateEvidence | None) -> str:
        if candidate is None:
            return ""

        locator = candidate.userLocator
        headings = CSVRenderer._unique_non_empty(locator.headingPath)
        nearest_heading = CSVRenderer._normalize_text(locator.nearestHeading)
        if nearest_heading and (not headings or headings[-1] != nearest_heading):
            headings.append(nearest_heading)

        location = " / ".join(headings)
        hint = CSVRenderer._normalize_text(locator.locatorHint)
        if hint and CSVRenderer._location_key(hint) != CSVRenderer._location_key(location):
            location = f"{location}；{hint}" if location else hint

        return location or "未定位到明确章节"

    @staticmethod
    def _build_excerpt(candidate: CandidateEvidence | None) -> str:
        if candidate is None:
            return ""

        parts = []
        for value in (
            candidate.preContext,
            candidate.exactText,
            candidate.postContext,
        ):
            normalized = CSVRenderer._normalize_text(value)
            if normalized and (not parts or parts[-1] != normalized):
                parts.append(normalized)

        excerpt = " ".join(parts)
        if len(excerpt) > MAX_EXCERPT_LENGTH:
            return excerpt[: MAX_EXCERPT_LENGTH - 1] + "…"
        return excerpt

    @staticmethod
    def _location_key(value: str) -> str:
        return re.sub(r"\s*[>/]\s*", "/", value).strip("/")
