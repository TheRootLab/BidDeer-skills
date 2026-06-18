from typing import List

from core.evidence_reasoning.models import EvidenceStatus, JudgedEvidencePackage
from core.report_renderer.models import (
    ChecklistReviewReport,
    ManualReviewItem,
    ReportSummary,
)


class ReportAggregator:
    @staticmethod
    def aggregate(packages: List[JudgedEvidencePackage]) -> ChecklistReviewReport:
        status_counts = {status.value: 0 for status in EvidenceStatus}
        manual_review_items: List[ManualReviewItem] = []

        for package in packages:
            status = package.result.status
            status_counts[status.value] += 1

            if status != EvidenceStatus.CLEAR_EVIDENCE:
                item = package.package.item
                manual_review_items.append(
                    ManualReviewItem(
                        itemId=item.itemId,
                        name=item.name,
                        status=status.value,
                        manualCheckPrompt=package.result.manualCheckPrompt,
                    )
                )

        summary = ReportSummary(
            totalItems=len(packages),
            statusCounts=status_counts,
            itemsRequiringManualReview=manual_review_items,
        )
        return ChecklistReviewReport(summary=summary, items=packages)
