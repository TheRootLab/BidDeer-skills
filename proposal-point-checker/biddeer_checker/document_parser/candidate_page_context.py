import re
from dataclasses import dataclass
from typing import List, Sequence

from biddeer_checker.evidence_retrieval.models import EvidencePackage


PDF_LOCATOR_PATTERN = re.compile(r"^(.+?) > 第 (-?\d+) 页$")


@dataclass(frozen=True)
class CandidatePageContext:
    source_page_num: int
    related_check_item_id: str
    nearby_text: str
    nearby_text_scope: str


def parse_pdf_page_locator(locator: str, expected_basename: str) -> int:
    match = PDF_LOCATOR_PATTERN.match(locator)
    if not match:
        raise ValueError(
            f"Cannot parse page number from locator: {locator!r}. "
            "Expected format: '<sourceDocName> > 第 <page-number> 页'"
        )

    document_name = match.group(1)
    if document_name != expected_basename:
        raise ValueError(
            f"Proposal basename mismatch: locator document name {document_name!r} "
            f"does not match expected basename {expected_basename!r}"
        )

    page_number = int(match.group(2))
    if page_number < 1:
        raise ValueError(
            f"Page number must be a positive integer, got {page_number}"
        )
    return page_number


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _build_context_text(candidate: object) -> str:
    parts = []
    for value in (
        candidate.preContext,
        candidate.exactText,
        candidate.postContext,
    ):
        if value:
            normalized = _normalize_text(value)
            if normalized:
                parts.append(normalized)
    return "\n".join(parts)


def adapt_to_candidate_contexts(
    proposal_basename: str,
    packages: Sequence[EvidencePackage],
) -> List[CandidatePageContext]:
    result: List[CandidatePageContext] = []
    seen_keys: set[tuple[str, int]] = set()

    for package in packages:
        item_id = package.item.itemId
        if not item_id or not item_id.strip():
            raise ValueError(
                "Empty or missing itemId in EvidencePackage "
                f"(name={package.item.name!r})"
            )

        page_fragments: dict[int, list[str]] = {}
        for candidate in package.candidates:
            page_number = parse_pdf_page_locator(
                candidate.userLocator.locatorHint,
                proposal_basename,
            )
            page_fragments.setdefault(page_number, []).append(
                _build_context_text(candidate)
            )

        for page_number in sorted(page_fragments):
            key = (item_id, page_number)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            unique_fragments = []
            seen_fragments: set[str] = set()
            for fragment in page_fragments[page_number]:
                if fragment not in seen_fragments:
                    seen_fragments.add(fragment)
                    unique_fragments.append(fragment)
            non_empty = [fragment for fragment in unique_fragments if fragment]

            if non_empty:
                nearby_text = "\n".join(non_empty)[:500]
                nearby_text_scope = "retrieval_context"
            else:
                nearby_text = ""
                nearby_text_scope = "none"

            result.append(
                CandidatePageContext(
                    source_page_num=page_number,
                    related_check_item_id=item_id,
                    nearby_text=nearby_text,
                    nearby_text_scope=nearby_text_scope,
                )
            )

    return result
