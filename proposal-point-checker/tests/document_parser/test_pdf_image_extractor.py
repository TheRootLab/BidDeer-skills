from pathlib import Path

import pytest

from biddeer_checker.document_parser.candidate_page_context import CandidatePageContext
from biddeer_checker.document_parser.pdf_image_extractor import (
    CONSENT_REQUIRED,
    DUPLICATE_IMAGE_OCCURRENCE,
    PILLOW_MISSING,
    PdfImageExtractor,
)
from tests.fixtures.generate_synthetic_pdf import (
    make_multi_page_test_pdf,
    make_test_pdf,
)


def _context(page: int, item: str, text: str = "retrieval context"):
    return CandidatePageContext(
        source_page_num=page,
        related_check_item_id=item,
        nearby_text=text,
        nearby_text_scope="retrieval_context" if text else "none",
    )


def test_targeted_extracts_only_candidate_page_images(tmp_path):
    pdf_path = make_multi_page_test_pdf(
        str(tmp_path / "proposal.pdf"),
        [
            [(4, 4, (255, 0, 0))],
            [(8, 8, (0, 255, 0))],
            [(12, 12, (0, 0, 255))],
        ],
    )

    items, warnings = PdfImageExtractor().extract_targeted(
        pdf_path=str(pdf_path),
        images_dir=str(tmp_path / "images"),
        candidate_contexts=[_context(1, "ITEM-001"), _context(3, "ITEM-003")],
    )

    assert warnings == []
    assert [(item.sourcePageNum, item.relatedCheckItemId) for item in items] == [
        (1, "ITEM-001"),
        (3, "ITEM-003"),
    ]
    assert sorted(path.name for path in (tmp_path / "images").iterdir()) == [
        "img_0001_01_01.png",
        "img_0003_01_01.png",
    ]


def test_multiple_items_on_one_page_create_separate_associations(tmp_path):
    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"))
    items, _warnings = PdfImageExtractor().extract_targeted(
        pdf_path=str(pdf_path),
        images_dir=str(tmp_path / "images"),
        candidate_contexts=[
            _context(1, "ITEM-A", "context A"),
            _context(1, "ITEM-B", "context B"),
        ],
    )

    assert [item.relatedCheckItemId for item in items] == ["ITEM-A", "ITEM-B"]
    assert [item.nearbyText for item in items] == ["context A", "context B"]
    assert all(item.recognitionState == CONSENT_REQUIRED for item in items)
    assert all(item.recognitionMethod == "none" for item in items)


def test_duplicate_candidate_context_does_not_duplicate_association(tmp_path):
    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"))
    duplicate = _context(1, "ITEM-001")
    items, _warnings = PdfImageExtractor().extract_targeted(
        pdf_path=str(pdf_path),
        images_dir=str(tmp_path / "images"),
        candidate_contexts=[duplicate, duplicate],
    )
    assert len(items) == 1


def test_duplicate_embedded_image_bytes_preserve_warning_semantics(tmp_path):
    pdf_path = make_test_pdf(
        str(tmp_path / "proposal.pdf"),
        [(4, 4, (255, 0, 0)), (4, 4, (255, 0, 0))],
    )
    items, _warnings = PdfImageExtractor().extract_targeted(
        pdf_path=str(pdf_path),
        images_dir=str(tmp_path / "images"),
        candidate_contexts=[_context(1, "ITEM-001")],
    )
    assert len(items) == 2
    assert items[0].imageSha256 == items[1].imageSha256
    assert DUPLICATE_IMAGE_OCCURRENCE in items[1].warnings


def test_targeted_uses_retrieval_context_without_page_text_lookup(tmp_path, monkeypatch):
    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"))
    monkeypatch.setattr(
        PdfImageExtractor,
        "_get_same_page_text",
        lambda *_args: pytest.fail("targeted mode must not extract page text"),
    )
    items, _warnings = PdfImageExtractor().extract_targeted(
        pdf_path=str(pdf_path),
        images_dir=str(tmp_path / "images"),
        candidate_contexts=[_context(1, "ITEM-001", "selected evidence")],
    )
    assert items[0].nearbyText == "selected evidence"
    assert items[0].nearbyTextScope == "retrieval_context"
    assert not Path(items[0].imagePath).is_absolute()


def test_targeted_missing_pillow_returns_unavailable_warning(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "biddeer_checker.document_parser.pdf_image_extractor._pillow_available",
        lambda: False,
    )
    items, warnings = PdfImageExtractor().extract_targeted(
        pdf_path="not-opened.pdf",
        images_dir=str(tmp_path / "images"),
        candidate_contexts=[_context(1, "ITEM-001")],
    )
    assert items == []
    assert warnings == [PILLOW_MISSING]
    assert not (tmp_path / "images").exists()


def test_invalid_candidate_page_fails_before_artifacts(tmp_path):
    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"))
    with pytest.raises(ValueError, match="out of range"):
        PdfImageExtractor().extract_targeted(
            pdf_path=str(pdf_path),
            images_dir=str(tmp_path / "images"),
            candidate_contexts=[_context(2, "ITEM-001")],
        )
    assert not (tmp_path / "images").exists()


def test_exhaustive_export_remains_unassigned_and_visits_all_pages(tmp_path):
    pdf_path = make_multi_page_test_pdf(
        str(tmp_path / "proposal.pdf"),
        [[(4, 4, (255, 0, 0))], [(8, 8, (0, 255, 0))]],
    )
    items, warnings = PdfImageExtractor().extract_exhaustive(
        pdf_path=str(pdf_path),
        images_dir=str(tmp_path / "images"),
    )
    assert warnings == []
    assert [item.sourcePageNum for item in items] == [1, 2]
    assert all(item.relatedCheckItemId == "UNASSIGNED" for item in items)
