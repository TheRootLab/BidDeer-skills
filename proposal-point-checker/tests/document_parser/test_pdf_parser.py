from pathlib import Path

import pytest

from biddeer_checker.document_parser.models import ParagraphBlock, ParsedDocument
from biddeer_checker.document_parser.pdf_parser import (
    MAX_BLOCK_CHARS,
    UNUSABLE_TEXT_ERROR,
    PdfDocumentParser,
)


FIXTURES = Path("tests/fixtures/pdf")


def test_parses_chinese_text_layer_pdf_into_bounded_blocks():
    document = PdfDocumentParser().parse(
        str(FIXTURES / "text_layer_chinese.pdf")
    )

    assert isinstance(document, ParsedDocument)
    assert document.images == []
    assert document.blocks
    assert all(isinstance(block, ParagraphBlock) for block in document.blocks)
    assert all(len(block.text) <= MAX_BLOCK_CHARS for block in document.blocks)
    assert "项目经理张三具备高级工程师职称" in "\n".join(
        block.text for block in document.blocks
    )


def test_preserves_one_based_page_provenance_without_cross_page_blocks():
    document = PdfDocumentParser().parse(
        str(FIXTURES / "multi_page_chinese.pdf")
    )

    first_page_blocks = [
        block
        for block in document.blocks
        if block.userLocator.locatorHint.endswith("第 1 页")
    ]
    second_page_blocks = [
        block
        for block in document.blocks
        if block.userLocator.locatorHint.endswith("第 2 页")
    ]

    assert first_page_blocks
    assert second_page_blocks
    assert all("第二页" not in block.text for block in first_page_blocks)
    assert all("第一页" not in block.text for block in second_page_blocks)
    assert all(block.userLocator.headingPath == [] for block in document.blocks)


def test_rejects_pdf_without_a_text_layer():
    with pytest.raises(
        ValueError,
        match="Scanned PDFs without a text layer are not supported in the MVP.",
    ):
        PdfDocumentParser().parse(str(FIXTURES / "image_only.pdf"))


def test_rejects_encrypted_pdf():
    with pytest.raises(
        PermissionError,
        match=(
            "The input PDF is encrypted or password-protected; "
            "decrypt it first."
        ),
    ):
        PdfDocumentParser().parse(str(FIXTURES / "encrypted.pdf"))


def test_retains_searchable_table_like_text():
    document = PdfDocumentParser().parse(
        str(FIXTURES / "table_like_text.pdf")
    )
    text = "\n".join(block.text for block in document.blocks)

    assert "信息安全管理体系认证证书" in text
    assert "2028年12月31日" in text


def test_uses_layout_extraction_for_multi_column_reading_order():
    document = PdfDocumentParser().parse(
        str(FIXTURES / "multi_page_chinese.pdf")
    )
    second_page_text = "\n".join(
        block.text
        for block in document.blocks
        if block.userLocator.locatorHint.endswith("第 2 页")
    )

    assert second_page_text.index("左栏内容") < second_page_text.index("右栏内容")


def test_splits_long_page_content_into_bounded_blocks():
    blocks = PdfDocumentParser()._split_page_text("证据" * MAX_BLOCK_CHARS)

    assert len(blocks) > 1
    assert all(len(block) <= MAX_BLOCK_CHARS for block in blocks)
    assert "".join(blocks) == "证据" * MAX_BLOCK_CHARS


def test_reports_page_extraction_failure_as_unusable_text(monkeypatch):
    class BrokenPage:
        def extract_text(self, extraction_mode):
            raise RuntimeError("synthetic extraction failure")

    class BrokenReader:
        is_encrypted = False
        pages = [BrokenPage()]

    monkeypatch.setattr(
        "biddeer_checker.document_parser.pdf_parser.PdfReader",
        lambda _path: BrokenReader(),
    )

    with pytest.raises(ValueError, match=UNUSABLE_TEXT_ERROR):
        PdfDocumentParser().parse("broken.pdf")
