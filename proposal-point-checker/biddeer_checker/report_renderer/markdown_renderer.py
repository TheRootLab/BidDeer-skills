from typing import List, Optional

from biddeer_checker.evidence_reasoning.models import EvidenceStatus, JudgedEvidencePackage
from biddeer_checker.evidence_retrieval.models import CandidateEvidence
from biddeer_checker.report_renderer.models import ChecklistReviewReport, ManualReviewItem


class MarkdownRenderer:
    @staticmethod
    def render(report: ChecklistReviewReport) -> str:
        lines: List[str] = []

        lines.extend(
            [
                "# 投标文件审核报告",
                "",
                "## 报告摘要",
                f"- 审核点总数: {report.summary.totalItems}",
                (
                    "- 需要人工重点复核: "
                    f"{len(report.summary.itemsRequiringManualReview)}"
                ),
                "",
                "## 状态统计",
            ]
        )
        for status in EvidenceStatus:
            lines.append(f"- {status.value}: {report.summary.statusCounts.get(status.value, 0)}")

        lines.extend(["", "## 重点复核清单"])
        if report.summary.itemsRequiringManualReview:
            for item in report.summary.itemsRequiringManualReview:
                lines.extend(MarkdownRenderer._render_manual_review_item(item))
        else:
            lines.append("- 无")

        lines.extend(["", "## 逐项检查结果"])
        if report.items:
            for judged_package in report.items:
                lines.extend(MarkdownRenderer._render_judged_package(judged_package))
        else:
            lines.append("- 无")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _render_manual_review_item(item: ManualReviewItem) -> List[str]:
        return [
            f"- {item.itemId}. {item.name}",
            f"  - 状态: {item.status}",
            f"  - 人工复核提示: {MarkdownRenderer._format_optional(item.manualCheckPrompt)}",
        ]

    @staticmethod
    def _render_judged_package(package: JudgedEvidencePackage) -> List[str]:
        checklist_item = package.package.item
        result = package.result
        lines = [
            f"### {checklist_item.itemId}. {checklist_item.name}",
            f"- 审核要求: {checklist_item.requirement}",
            f"- 审核说明: {MarkdownRenderer._format_optional(checklist_item.note)}",
            f"- 状态: {result.status.value}",
            f"- 判断依据: {MarkdownRenderer._format_optional(result.judgmentBasis)}",
            f"- 人工复核提示: {MarkdownRenderer._format_optional(result.manualCheckPrompt)}",
            "",
            "<details>",
            "<summary>候选证据与定位</summary>",
            "",
        ]

        if package.package.candidates:
            for index, candidate in enumerate(package.package.candidates, start=1):
                lines.extend(MarkdownRenderer._render_candidate(index, candidate))
        else:
            lines.append("- 无候选证据")

        lines.extend(["", "</details>", ""])
        return lines

    @staticmethod
    def _render_candidate(index: int, candidate: CandidateEvidence) -> List[str]:
        locator = candidate.userLocator
        heading_path = " > ".join(locator.headingPath) if locator.headingPath else "-"
        image_ids = ", ".join(image.imageId for image in candidate.nearbyImages) or "-"
        row_index = MarkdownRenderer._format_optional_number(candidate.rowIndex)

        return [
            f"#### 候选证据 {index}",
            f"- matchedKeywords: {', '.join(candidate.matchedKeywords) or '-'}",
            f"- exactText: {MarkdownRenderer._format_optional(candidate.exactText)}",
            f"- preContext: {MarkdownRenderer._format_optional(candidate.preContext)}",
            f"- postContext: {MarkdownRenderer._format_optional(candidate.postContext)}",
            f"- sourceDocName: {MarkdownRenderer._format_optional(locator.sourceDocName)}",
            f"- headingPath: {heading_path}",
            f"- nearestHeading: {MarkdownRenderer._format_optional(locator.nearestHeading)}",
            f"- nearbyText: {MarkdownRenderer._format_optional(locator.nearbyText)}",
            f"- locatorHint: {MarkdownRenderer._format_optional(locator.locatorHint)}",
            f"- evidenceType: {MarkdownRenderer._format_optional(locator.evidenceType)}",
            f"- blockIndex: {candidate.blockIndex}",
            f"- rowIndex: {row_index}",
            f"- imageId: {image_ids}",
            "",
        ]

    @staticmethod
    def _format_optional(value: Optional[str]) -> str:
        if value is None or value == "":
            return "-"
        return value

    @staticmethod
    def _format_optional_number(value: Optional[int]) -> str:
        if value is None:
            return "-"
        return str(value)
