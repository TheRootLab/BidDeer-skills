from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChecklistItem:
    itemId: str
    name: str
    requirement: str
    note: str


@dataclass(frozen=True)
class CSVParseError:
    errorCode: str
    message: str
    rowNumber: Optional[int]
    fieldName: Optional[str]
    suggestion: Optional[str]
