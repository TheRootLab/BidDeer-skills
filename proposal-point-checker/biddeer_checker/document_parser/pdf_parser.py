from pathlib import Path
from typing import List

from pypdf import PdfReader

from biddeer_checker.document_parser.models import (
    DocumentBlock,
    InternalTraceLocator,
    ParagraphBlock,
    ParsedDocument,
    UserFacingLocator,
)


MAX_BLOCK_CHARS = 2000
ENCRYPTED_PDF_ERROR = (
    "The input PDF is encrypted or password-protected; decrypt it first."
)
NO_TEXT_LAYER_ERROR = (
    "Scanned PDFs without a text layer are not supported in the MVP."
)
UNUSABLE_TEXT_ERROR = (
    "PDF text extraction failed or produced unusable text; "
    "provide a text-layer PDF."
)


class PdfDocumentParser:
    def parse(self, file_path: str) -> ParsedDocument:
        try:
            reader = PdfReader(file_path)
        except Exception as error:
            raise ValueError(UNUSABLE_TEXT_ERROR) from error

        if reader.is_encrypted:
            raise PermissionError(ENCRYPTED_PDF_ERROR)

        source_name = Path(file_path).name
        blocks: List[DocumentBlock] = []
        has_usable_text = False

        try:
            for page_number, page in enumerate(reader.pages, start=1):
                page_text = self._extract_page_text(page)
                if page_text.strip():
                    has_usable_text = True
                for block_text in self._split_page_text(page_text):
                    block_index = len(blocks)
                    blocks.append(
                        ParagraphBlock(
                            blockIndex=block_index,
                            userLocator=UserFacingLocator(
                                sourceDocName=source_name,
                                headingPath=[],
                                nearestHeading=None,
                                nearbyText=block_text,
                                locatorHint=(
                                    f"{source_name} > 第 {page_number} 页"
                                ),
                                evidenceType="TEXT",
                            ),
                            traceLocator=InternalTraceLocator(
                                blockIndex=block_index
                            ),
                            text=block_text,
                        )
                    )
        except Exception as error:
            raise ValueError(UNUSABLE_TEXT_ERROR) from error

        if not has_usable_text:
            raise ValueError(NO_TEXT_LAYER_ERROR)

        return ParsedDocument(blocks=blocks, images=[])

    def _extract_page_text(self, page: object) -> str:
        extracted = page.extract_text(extraction_mode="layout") or ""
        normalized_newlines = extracted.replace("\r\n", "\n").replace(
            "\r", "\n"
        )
        return "\n".join(
            line.rstrip() for line in normalized_newlines.split("\n")
        ).strip()

    def _split_page_text(self, page_text: str) -> List[str]:
        paragraphs: List[str] = []
        current_lines: List[str] = []

        for line in page_text.split("\n"):
            if line.strip():
                current_lines.append(line)
            elif current_lines:
                paragraphs.extend(self._split_long_block(current_lines))
                current_lines = []

        if current_lines:
            paragraphs.extend(self._split_long_block(current_lines))

        return paragraphs

    def _split_long_block(self, lines: List[str]) -> List[str]:
        blocks: List[str] = []
        current = ""

        for line in lines:
            for segment in self._split_long_line(line):
                candidate = f"{current}\n{segment}" if current else segment
                if len(candidate) <= MAX_BLOCK_CHARS:
                    current = candidate
                else:
                    if current:
                        blocks.append(current)
                    current = segment

        if current:
            blocks.append(current)

        return blocks

    def _split_long_line(self, line: str) -> List[str]:
        return [
            line[index : index + MAX_BLOCK_CHARS]
            for index in range(0, len(line), MAX_BLOCK_CHARS)
        ]
