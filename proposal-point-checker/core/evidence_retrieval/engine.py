from typing import List, Optional

from core.checklist_model.models import ChecklistItem
from core.document_parser.models import (
    DocumentBlock,
    ParagraphBlock,
    ParsedDocument,
    TableBlock,
)
from core.evidence_retrieval.models import CandidateEvidence, EvidencePackage
from core.evidence_retrieval.query_expansion import (
    CHINESE_DOMAIN_PHRASES,
    _normalize_text,
    expand_query,
)


STRONG_CHINESE_DOMAIN_TERMS = {
    _normalize_text(phrase)
    for phrase in CHINESE_DOMAIN_PHRASES
    if len(_normalize_text(phrase)) >= 3
}


def _has_strong_match(matched_keywords: List[str]) -> bool:
    return any(
        len(keyword) >= 4
        or any(character.isdigit() for character in keyword)
        or keyword in STRONG_CHINESE_DOMAIN_TERMS
        for keyword in matched_keywords
    )


def _get_block_text(block: DocumentBlock) -> str:
    if isinstance(block, ParagraphBlock):
        return block.text
    if isinstance(block, TableBlock):
        return block.tableText
    return ""


def _build_candidate(
    block: DocumentBlock,
    matched_keywords: List[str],
    doc: ParsedDocument,
    block_position: int,
    row_index: Optional[int] = None,
) -> CandidateEvidence:
    pre_context = (
        _get_block_text(doc.blocks[block_position - 1])
        if block_position > 0
        else ""
    )
    post_context = (
        _get_block_text(doc.blocks[block_position + 1])
        if block_position < len(doc.blocks) - 1
        else ""
    )
    exact_text = ""
    nearby_images = []

    if isinstance(block, ParagraphBlock):
        exact_text = block.text
        nearby_images.extend(block.images)
    elif isinstance(block, TableBlock) and row_index is not None:
        exact_text = " | ".join(block.rows[row_index])
        if row_index > 0 and block.rows:
            pre_context = f"【表头】{' | '.join(block.rows[0])}\n{pre_context}"

    return CandidateEvidence(
        blockIndex=block.blockIndex,
        rowIndex=row_index,
        userLocator=block.userLocator,
        matchedKeywords=matched_keywords,
        exactText=exact_text,
        preContext=pre_context,
        postContext=post_context,
        nearbyImages=nearby_images,
    )


def retrieve_evidence(
    items: List[ChecklistItem],
    doc: ParsedDocument,
) -> List[EvidencePackage]:
    packages = []

    for item in items:
        keywords = expand_query(item)
        scored_blocks = []

        for block_position, block in enumerate(doc.blocks):
            if isinstance(block, ParagraphBlock):
                text = _normalize_text(block.text)
                matched = [keyword for keyword in keywords if keyword in text]
                if matched and _has_strong_match(matched):
                    scored_blocks.append(
                        (len(matched), block_position, block, None, matched)
                    )
            elif isinstance(block, TableBlock):
                for row_index, row in enumerate(block.rows):
                    if row_index == 0:
                        continue
                    row_text = _normalize_text(" ".join(row))
                    matched = [keyword for keyword in keywords if keyword in row_text]
                    if matched and _has_strong_match(matched):
                        scored_blocks.append(
                            (
                                len(matched),
                                block_position,
                                block,
                                row_index,
                                matched,
                            )
                        )

        scored_blocks.sort(
            key=lambda item_score: (
                item_score[0],
                len(_get_block_text(item_score[2])),
            ),
            reverse=True,
        )

        candidates = []
        seen_blocks = set()
        for _score, block_position, block, row_index, matched in scored_blocks:
            if len(candidates) >= 5:
                break

            dedup_key = (block.blockIndex, row_index)
            is_redundant = False
            if isinstance(block, ParagraphBlock):
                is_redundant = any(
                    abs(candidate.blockIndex - block.blockIndex) <= 1
                    for candidate in candidates
                )

            if is_redundant or dedup_key in seen_blocks:
                continue

            seen_blocks.add(dedup_key)
            candidates.append(
                _build_candidate(block, matched, doc, block_position, row_index)
            )
        packages.append(EvidencePackage(item=item, candidates=candidates))

    return packages
