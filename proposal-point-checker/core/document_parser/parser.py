from pathlib import Path
import re
from typing import List, Optional

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from core.document_parser.models import (
    DocumentBlock,
    ImageObject,
    InternalTraceLocator,
    ParagraphBlock,
    ParsedDocument,
    TableBlock,
    UnsupportedBlock,
    UserFacingLocator,
)


class DocxDocumentParser:
    def parse(self, file_path: str) -> ParsedDocument:
        document = Document(file_path)
        source_name = Path(file_path).name
        blocks: List[DocumentBlock] = []
        images: List[ImageObject] = []
        heading_stack: List[Optional[str]] = [None] * 6
        paragraph_index = 0
        table_index = 0

        for child in document.element.body.iterchildren():
            if child.tag == qn("w:p"):
                paragraph = Paragraph(child, document)
                heading_level = self._heading_level(paragraph)
                if heading_level is not None:
                    heading_stack[heading_level - 1] = paragraph.text.strip()
                    for level in range(heading_level, len(heading_stack)):
                        heading_stack[level] = None

                heading_path = self._current_heading_path(heading_stack)
                block_index = len(blocks)
                paragraph_images = self._extract_images(
                    paragraph=paragraph,
                    block_index=block_index,
                    paragraph_index=paragraph_index,
                    image_start_index=len(images),
                )
                images.extend(paragraph_images)

                blocks.append(
                    ParagraphBlock(
                        blockIndex=block_index,
                        userLocator=self._user_locator(
                            source_name=source_name,
                            heading_path=heading_path,
                            nearby_text=paragraph.text.strip(),
                            evidence_type="paragraph",
                            has_images=bool(paragraph_images),
                        ),
                        traceLocator=InternalTraceLocator(
                            blockIndex=block_index,
                            paragraphIndex=paragraph_index,
                            imageIndex=(
                                len(images) - len(paragraph_images)
                                if paragraph_images
                                else None
                            ),
                            relationshipId=(
                                paragraph_images[0].relationshipId
                                if paragraph_images
                                else None
                            ),
                        ),
                        text=paragraph.text,
                        images=paragraph_images,
                    )
                )
                paragraph_index += 1
            elif child.tag == qn("w:tbl"):
                table = Table(child, document)
                rows = self._table_rows(table)
                table_text = "\n".join("\t".join(row) for row in rows)
                block_index = len(blocks)
                blocks.append(
                    TableBlock(
                        blockIndex=block_index,
                        userLocator=self._user_locator(
                            source_name=source_name,
                            heading_path=self._current_heading_path(heading_stack),
                            nearby_text=table_text,
                            evidence_type="table",
                            has_images=False,
                        ),
                        traceLocator=InternalTraceLocator(
                            blockIndex=block_index,
                            tableIndex=table_index,
                            rowIndex=None,
                        ),
                        rows=rows,
                        tableText=table_text,
                    )
                )
                table_index += 1
            elif child.tag != qn("w:sectPr"):
                block_index = len(blocks)
                blocks.append(
                    UnsupportedBlock(
                        blockIndex=block_index,
                        userLocator=self._user_locator(
                            source_name=source_name,
                            heading_path=self._current_heading_path(heading_stack),
                            nearby_text="",
                            evidence_type="unsupported",
                            has_images=False,
                        ),
                        traceLocator=InternalTraceLocator(blockIndex=block_index),
                        xml_tag=child.tag,
                    )
                )

        return ParsedDocument(blocks=blocks, images=images)

    def _heading_level(self, paragraph: Paragraph) -> Optional[int]:
        style_name = paragraph.style.name if paragraph.style is not None else ""
        match = re.fullmatch(r"(?:Heading|标题)\s*([1-6])", style_name)
        if match:
            return int(match.group(1))
        return None

    def _current_heading_path(self, heading_stack: List[Optional[str]]) -> List[str]:
        return [heading for heading in heading_stack if heading]

    def _user_locator(
        self,
        source_name: str,
        heading_path: List[str],
        nearby_text: str,
        evidence_type: str,
        has_images: bool,
    ) -> UserFacingLocator:
        locator_hint = "请根据标题路径和附近文本定位该内容。"
        if has_images:
            locator_hint = "请根据标题路径、附近文本，并检查该段落附近图片。"

        return UserFacingLocator(
            sourceDocName=source_name,
            headingPath=list(heading_path),
            nearestHeading=heading_path[-1] if heading_path else None,
            nearbyText=nearby_text,
            locatorHint=locator_hint,
            evidenceType=evidence_type,
        )

    def _table_rows(self, table: Table) -> List[List[str]]:
        return [
            [cell.text.strip() for cell in row.cells]
            for row in table.rows
        ]

    def _extract_images(
        self,
        paragraph: Paragraph,
        block_index: int,
        paragraph_index: int,
        image_start_index: int,
    ) -> List[ImageObject]:
        image_objects: List[ImageObject] = []
        relationship_ids = paragraph._p.xpath(".//a:blip/@r:embed")
        nearby_text = paragraph.text.strip()

        for offset, relationship_id in enumerate(relationship_ids):
            image_index = image_start_index + offset
            image_objects.append(
                ImageObject(
                    imageId=f"image-{image_index + 1}",
                    anchorBlockIndex=block_index,
                    anchorParagraphIndex=paragraph_index,
                    nearbyText=nearby_text,
                    relationshipId=relationship_id,
                )
            )

        return image_objects
