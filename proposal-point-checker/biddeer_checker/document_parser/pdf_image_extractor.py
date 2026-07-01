import hashlib
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from biddeer_checker.document_parser.candidate_page_context import (
    CandidatePageContext,
)


EXTRACTION_UNAVAILABLE = "EXTRACTION_UNAVAILABLE"
CONSENT_REQUIRED = "CONSENT_REQUIRED"
EXTRACTION_FAILED = "EXTRACTION_FAILED"

PILLOW_MISSING = "PILLOW_MISSING"
IMAGE_EXTRACTION_FAILED = "IMAGE_EXTRACTION_FAILED"
UNSUPPORTED_IMAGE_ENCODING = "UNSUPPORTED_IMAGE_ENCODING"
DUPLICATE_IMAGE_OCCURRENCE = "DUPLICATE_IMAGE_OCCURRENCE"
SMALL_DECORATIVE_IMAGE_POSSIBLE = "SMALL_DECORATIVE_IMAGE_POSSIBLE"
NO_TEXT_CONTEXT_AVAILABLE = "NO_TEXT_CONTEXT_AVAILABLE"
BBOX_UNAVAILABLE = "BBOX_UNAVAILABLE"
SCANNED_PAGE_NOT_FULLY_SUPPORTED = "SCANNED_PAGE_NOT_FULLY_SUPPORTED"
LOCAL_PROVIDER_NOT_CONFIGURED = "LOCAL_PROVIDER_NOT_CONFIGURED"
ONLINE_REVIEW_REQUIRES_CONSENT = "ONLINE_REVIEW_REQUIRES_CONSENT"

EXTRACTION_STATE_COMPLETED = "completed"
EXTRACTION_STATE_UNAVAILABLE = "unavailable"
EXTRACTION_STATE_PARTIAL = "partial"


@dataclass
class ExtractedImage:
    sourcePageNum: int
    imageIndex: int
    imageId: str
    traceId: str
    imagePath: Optional[str] = None
    imageSha256: Optional[str] = None
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None
    imageFormat: Optional[str] = None
    extractionMethod: str = "embedded_image"
    recognitionState: str = CONSENT_REQUIRED
    recognitionMethod: str = "none"
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    relatedCheckItemId: str = "UNASSIGNED"
    nearbyText: str = ""
    nearbyTextScope: str = "none"


def _pillow_available() -> bool:
    try:
        import PIL  # noqa: F401

        return True
    except ImportError:
        return False


def _synthetic_trace_id() -> str:
    return f"trace-{uuid.uuid4().hex[:12]}"


def _compute_sha256(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


class PdfImageExtractor:
    def __init__(self) -> None:
        self._pillow = _pillow_available()

    def pillow_available(self) -> bool:
        return self._pillow

    def extract_exhaustive(
        self,
        pdf_path: str,
        images_dir: str,
    ) -> Tuple[List[ExtractedImage], List[str]]:
        if not self._pillow:
            return [], [PILLOW_MISSING]

        from pypdf import PdfReader

        items: List[ExtractedImage] = []
        reader = PdfReader(pdf_path)
        output_dir = Path(images_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_sha256s: set[str] = set()

        for page_number, page in enumerate(reader.pages, start=1):
            page_images = list(page.images)
            if not page_images:
                continue
            same_page_text = self._get_same_page_text(page)
            for image_index, image in enumerate(page_images, start=1):
                item = self._extract_single_image(
                    image=image,
                    page_number=page_number,
                    image_index=image_index,
                    output_dir=output_dir,
                    nearby_text=same_page_text,
                    nearby_text_scope="same_page" if same_page_text else "none",
                    image_id=f"img_{page_number:04d}_{image_index:02d}",
                    related_check_item_id="UNASSIGNED",
                )
                self._record_duplicate(item, seen_sha256s)
                items.append(item)
        return items, []

    def extract_targeted(
        self,
        pdf_path: str,
        images_dir: str,
        candidate_contexts: List[CandidatePageContext],
    ) -> Tuple[List[ExtractedImage], List[str]]:
        if not self._pillow:
            return [], [PILLOW_MISSING]

        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        for context in candidate_contexts:
            if (
                context.source_page_num < 1
                or context.source_page_num > page_count
            ):
                raise ValueError(
                    f"Candidate page number {context.source_page_num} is out of "
                    f"range (PDF has {page_count} pages)"
                )

        deduplicated_contexts = []
        seen_contexts: set[tuple[str, int]] = set()
        for context in candidate_contexts:
            key = (
                context.related_check_item_id,
                context.source_page_num,
            )
            if key not in seen_contexts:
                seen_contexts.add(key)
                deduplicated_contexts.append(context)

        contexts_by_page: dict[int, list[CandidatePageContext]] = defaultdict(list)
        for context in deduplicated_contexts:
            contexts_by_page[context.source_page_num].append(context)

        output_dir = Path(images_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        items: List[ExtractedImage] = []
        seen_sha256s: set[str] = set()

        for page_number in sorted(contexts_by_page):
            page_images = list(reader.pages[page_number - 1].images)
            for image_index, image in enumerate(page_images, start=1):
                for association_index, context in enumerate(
                    contexts_by_page[page_number],
                    start=1,
                ):
                    image_id = (
                        f"img_{page_number:04d}_{image_index:02d}_"
                        f"{association_index:02d}"
                    )
                    item = self._extract_single_image(
                        image=image,
                        page_number=page_number,
                        image_index=image_index,
                        output_dir=output_dir,
                        nearby_text=context.nearby_text,
                        nearby_text_scope=context.nearby_text_scope,
                        image_id=image_id,
                        related_check_item_id=context.related_check_item_id,
                    )
                    self._record_duplicate(item, seen_sha256s)
                    items.append(item)
        return items, []

    @staticmethod
    def _record_duplicate(
        item: ExtractedImage,
        seen_sha256s: set[str],
    ) -> None:
        if item.imageSha256 and item.imageSha256 in seen_sha256s:
            if DUPLICATE_IMAGE_OCCURRENCE not in item.warnings:
                item.warnings.append(DUPLICATE_IMAGE_OCCURRENCE)
        if item.imageSha256:
            seen_sha256s.add(item.imageSha256)

    def _extract_single_image(
        self,
        *,
        image: object,
        page_number: int,
        image_index: int,
        output_dir: Path,
        nearby_text: str,
        nearby_text_scope: str,
        image_id: str,
        related_check_item_id: str,
    ) -> ExtractedImage:
        item = ExtractedImage(
            sourcePageNum=page_number,
            imageIndex=image_index,
            imageId=image_id,
            traceId=_synthetic_trace_id(),
            relatedCheckItemId=related_check_item_id,
            nearbyText=nearby_text,
            nearbyTextScope=nearby_text_scope,
        )
        if not nearby_text:
            item.warnings.append(NO_TEXT_CONTEXT_AVAILABLE)

        try:
            pillow_image = image.image
            image_format = pillow_image.format or "PNG"
            extension = self._format_to_extension(image_format)
            filename = f"{image_id}{extension}"
            image_path = output_dir / filename
            pillow_image.save(str(image_path))
        except Exception as error:
            item.recognitionState = EXTRACTION_FAILED
            item.warnings.append(IMAGE_EXTRACTION_FAILED)
            item.error = str(error)
            return item

        item.imagePath = f"images/{filename}"
        item.imageSha256 = _compute_sha256(image_path)
        item.imageWidth = pillow_image.width
        item.imageHeight = pillow_image.height
        item.imageFormat = image_format
        if pillow_image.width < 100 or pillow_image.height < 100:
            item.warnings.append(SMALL_DECORATIVE_IMAGE_POSSIBLE)
        item.warnings.extend(
            [
                LOCAL_PROVIDER_NOT_CONFIGURED,
                ONLINE_REVIEW_REQUIRES_CONSENT,
            ]
        )
        return item

    @staticmethod
    def _get_same_page_text(page: object) -> str:
        try:
            return (page.extract_text(extraction_mode="layout") or "").strip()[:500]
        except Exception:
            return ""

    @staticmethod
    def _format_to_extension(image_format: str) -> str:
        return {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif",
            "BMP": ".bmp",
            "TIFF": ".tiff",
            "WEBP": ".webp",
        }.get(image_format.upper(), ".png")
