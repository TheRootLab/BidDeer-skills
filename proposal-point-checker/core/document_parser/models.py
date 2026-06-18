from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class UserFacingLocator:
    sourceDocName: str
    headingPath: List[str]
    nearestHeading: Optional[str]
    nearbyText: str
    locatorHint: str
    evidenceType: str


@dataclass(frozen=True)
class InternalTraceLocator:
    blockIndex: int
    paragraphIndex: Optional[int] = None
    tableIndex: Optional[int] = None
    rowIndex: Optional[int] = None
    imageIndex: Optional[int] = None
    relationshipId: Optional[str] = None


@dataclass(frozen=True)
class ImageObject:
    imageId: str
    anchorBlockIndex: int
    anchorParagraphIndex: Optional[int]
    nearbyText: str
    relationshipId: str
    contentRecognized: bool = False
    reason: str = "IMAGE_CONTENT_NOT_RECOGNIZED"


@dataclass
class DocumentBlock:
    blockIndex: int
    userLocator: UserFacingLocator
    traceLocator: InternalTraceLocator


@dataclass
class ParagraphBlock(DocumentBlock):
    text: str
    images: List[ImageObject] = field(default_factory=list)


@dataclass
class TableBlock(DocumentBlock):
    rows: List[List[str]]
    tableText: str


@dataclass
class UnsupportedBlock(DocumentBlock):
    xml_tag: str


@dataclass
class ParsedDocument:
    blocks: List[DocumentBlock]
    images: List[ImageObject]
