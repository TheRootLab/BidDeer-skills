from dataclasses import dataclass
from typing import Dict, List

from biddeer_checker.evidence_reasoning.models import JudgedEvidencePackage


@dataclass
class ManualReviewItem:
    itemId: str
    name: str
    status: str
    manualCheckPrompt: str


@dataclass
class ReportSummary:
    totalItems: int
    statusCounts: Dict[str, int]
    itemsRequiringManualReview: List[ManualReviewItem]


@dataclass
class ChecklistReviewReport:
    summary: ReportSummary
    items: List[JudgedEvidencePackage]
