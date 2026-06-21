from dataclasses import dataclass, field
from typing import List, Optional

from biddeer_checker.checklist_model.models import ChecklistItem
from biddeer_checker.document_parser.models import ImageObject, UserFacingLocator


@dataclass
class CandidateEvidence:
    """Single candidate evidence fragment."""

    blockIndex: int
    userLocator: UserFacingLocator
    matchedKeywords: List[str]
    exactText: str
    preContext: str
    postContext: str
    nearbyImages: List[ImageObject]
    rowIndex: Optional[int] = None


@dataclass
class EvidencePackage:
    """Evidence package for one checklist item."""

    item: ChecklistItem
    candidates: List[CandidateEvidence] = field(default_factory=list)
