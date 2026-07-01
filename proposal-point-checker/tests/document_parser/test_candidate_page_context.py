import pytest

from biddeer_checker.checklist_model.models import ChecklistItem
from biddeer_checker.document_parser.candidate_page_context import (
    adapt_to_candidate_contexts,
    parse_pdf_page_locator,
)
from biddeer_checker.document_parser.models import UserFacingLocator
from biddeer_checker.evidence_retrieval.models import CandidateEvidence, EvidencePackage


BASENAME = "proposal.pdf"


def _candidate(
    locator: str,
    *,
    exact: str = "exact",
    pre: str = "",
    post: str = "",
    block_index: int = 0,
) -> CandidateEvidence:
    return CandidateEvidence(
        blockIndex=block_index,
        userLocator=UserFacingLocator(
            sourceDocName=BASENAME,
            headingPath=[],
            nearestHeading=None,
            nearbyText=exact,
            locatorHint=locator,
            evidenceType="TEXT",
        ),
        matchedKeywords=[],
        exactText=exact,
        preContext=pre,
        postContext=post,
        nearbyImages=[],
    )


def _package(item_id: str, candidates: list[CandidateEvidence]) -> EvidencePackage:
    return EvidencePackage(
        item=ChecklistItem(
            itemId=item_id,
            name="item",
            requirement="requirement",
            note="",
        ),
        candidates=candidates,
    )


def test_parse_canonical_locator_and_reject_basename_mismatch():
    assert parse_pdf_page_locator("proposal.pdf > 第 12 页", BASENAME) == 12
    with pytest.raises(ValueError, match="basename mismatch"):
        parse_pdf_page_locator("other.pdf > 第 12 页", BASENAME)


@pytest.mark.parametrize(
    "locator, message",
    [
        ("proposal.pdf > 第 0 页", "positive integer"),
        ("proposal.pdf > 第 -1 页", "positive integer"),
        ("proposal.pdf > 第 x 页", "Cannot parse"),
        ("page 7 in arbitrary text", "Cannot parse"),
        ("", "Cannot parse"),
    ],
)
def test_rejects_invalid_or_noncanonical_page_locators(locator, message):
    with pytest.raises(ValueError, match=message):
        parse_pdf_page_locator(locator, BASENAME)


def test_adapter_does_not_infer_page_from_block_index():
    package = _package(
        "ITEM-001",
        [_candidate("not a PDF locator", block_index=99)],
    )
    with pytest.raises(ValueError, match="Cannot parse"):
        adapt_to_candidate_contexts(BASENAME, [package])


def test_empty_item_id_fails():
    with pytest.raises(ValueError, match="Empty or missing itemId"):
        adapt_to_candidate_contexts(
            BASENAME,
            [_package("", [_candidate("proposal.pdf > 第 1 页")])],
        )


def test_context_assembly_deduplication_and_truncation():
    repeated = "x" * 300
    package = _package(
        "ITEM-001",
        [
            _candidate(
                "proposal.pdf > 第 2 页",
                pre=" before\r\n",
                exact=repeated,
                post="after ",
            ),
            _candidate(
                "proposal.pdf > 第 2 页",
                pre=" before\r\n",
                exact=repeated,
                post="after ",
            ),
            _candidate("proposal.pdf > 第 2 页", exact="y" * 300),
        ],
    )

    contexts = adapt_to_candidate_contexts(BASENAME, [package])

    assert len(contexts) == 1
    assert contexts[0].source_page_num == 2
    assert contexts[0].related_check_item_id == "ITEM-001"
    assert contexts[0].nearby_text.startswith("before\n" + repeated + "\nafter")
    assert len(contexts[0].nearby_text) == 500
    assert contexts[0].nearby_text_scope == "retrieval_context"


def test_adapter_preserves_multiple_items_and_pages():
    contexts = adapt_to_candidate_contexts(
        BASENAME,
        [
            _package(
                "ITEM-A",
                [
                    _candidate("proposal.pdf > 第 3 页", exact="page 3"),
                    _candidate("proposal.pdf > 第 1 页", exact="page 1"),
                ],
            ),
            _package(
                "ITEM-B",
                [_candidate("proposal.pdf > 第 1 页", exact="other item")],
            ),
        ],
    )

    assert [
        (context.related_check_item_id, context.source_page_num)
        for context in contexts
    ] == [("ITEM-A", 1), ("ITEM-A", 3), ("ITEM-B", 1)]


def test_empty_retrieval_context_uses_none_scope():
    contexts = adapt_to_candidate_contexts(
        BASENAME,
        [_package("ITEM-001", [_candidate("proposal.pdf > 第 1 页", exact="")])],
    )
    assert contexts[0].nearby_text == ""
    assert contexts[0].nearby_text_scope == "none"
