from dataclasses import dataclass
from enum import Enum

from biddeer_checker.evidence_retrieval.models import EvidencePackage


class EvidenceStatus(Enum):
    CLEAR_EVIDENCE = "CLEAR_EVIDENCE"
    SUSPECTED_EVIDENCE = "SUSPECTED_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNABLE_TO_JUDGE = "UNABLE_TO_JUDGE"


@dataclass
class ReasoningResult:
    status: EvidenceStatus
    reason: str
    judgmentBasis: str
    manualCheckPrompt: str


@dataclass
class JudgedEvidencePackage:
    package: EvidencePackage
    result: ReasoningResult
