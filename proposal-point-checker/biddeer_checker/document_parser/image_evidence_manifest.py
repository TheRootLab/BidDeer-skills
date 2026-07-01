import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from biddeer_checker.document_parser.pdf_image_extractor import (
    EXTRACTION_FAILED,
    EXTRACTION_STATE_COMPLETED,
    EXTRACTION_STATE_PARTIAL,
    EXTRACTION_STATE_UNAVAILABLE,
    EXTRACTION_UNAVAILABLE,
    PILLOW_MISSING,
    ExtractedImage,
)


MANIFEST_VERSION = "image-evidence-v0.1"


def _get_pypdf_version() -> str:
    try:
        import pypdf

        return pypdf.__version__
    except ImportError:
        return "unknown"


def _get_pillow_version() -> Optional[str]:
    try:
        import PIL

        return PIL.__version__
    except ImportError:
        return None


def serialize_item(
    item: ExtractedImage,
    source_doc_name: str,
) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {
        "manifestVersion": MANIFEST_VERSION,
        "sourceDocName": source_doc_name,
        "sourcePageNum": item.sourcePageNum,
        "imageId": item.imageId,
        "relatedCheckItemId": item.relatedCheckItemId,
        "nearbyText": item.nearbyText,
        "nearbyTextScope": item.nearbyTextScope,
        "extractionMethod": item.extractionMethod,
        "recognitionState": item.recognitionState,
        "recognitionMethod": item.recognitionMethod,
        "warnings": item.warnings,
        "traceId": item.traceId,
    }
    if item.recognitionState not in (EXTRACTION_FAILED, EXTRACTION_UNAVAILABLE):
        serialized.update(
            {
                "imagePath": item.imagePath,
                "imageSha256": item.imageSha256,
                "imageWidth": item.imageWidth,
                "imageHeight": item.imageHeight,
                "imageFormat": item.imageFormat,
            }
        )
    if item.error is not None:
        serialized["error"] = item.error
    return serialized


def build_manifest(
    source_doc_name: str,
    extraction_mode: str,
    items: List[ExtractedImage],
    global_warnings: List[str],
    extraction_state: str = EXTRACTION_STATE_COMPLETED,
) -> Dict[str, Any]:
    return {
        "manifestVersion": MANIFEST_VERSION,
        "sourceDocName": source_doc_name,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "extractionMode": extraction_mode,
        "extractionState": extraction_state,
        "imageRuntime": {
            "pdfLibrary": "pypdf",
            "pdfLibraryVersion": _get_pypdf_version(),
            "imageDependency": "Pillow",
            "imageDependencyVersion": _get_pillow_version(),
        },
        "items": [serialize_item(item, source_doc_name) for item in items],
        "warnings": global_warnings,
    }


def _derive_extraction_state(
    items: List[ExtractedImage],
    global_warnings: List[str],
) -> str:
    if PILLOW_MISSING in global_warnings:
        return EXTRACTION_STATE_UNAVAILABLE
    failed_count = sum(
        item.recognitionState == EXTRACTION_FAILED for item in items
    )
    if failed_count and failed_count < len(items):
        return EXTRACTION_STATE_PARTIAL
    if failed_count and failed_count == len(items):
        return EXTRACTION_STATE_UNAVAILABLE
    return EXTRACTION_STATE_COMPLETED


def write_manifest_and_images(
    workspace_dir: str,
    source_doc_name: str,
    extraction_mode: str,
    items: List[ExtractedImage],
    global_warnings: List[str],
) -> str:
    manifest = build_manifest(
        source_doc_name=source_doc_name,
        extraction_mode=extraction_mode,
        items=items,
        global_warnings=global_warnings,
        extraction_state=_derive_extraction_state(items, global_warnings),
    )
    manifest_path = Path(workspace_dir) / "image_evidence_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(manifest_path)


def write_pillow_missing_manifest(
    workspace_dir: str,
    source_doc_name: str,
    extraction_mode: str = "exhaustive_export",
) -> str:
    return write_manifest_and_images(
        workspace_dir=workspace_dir,
        source_doc_name=source_doc_name,
        extraction_mode=extraction_mode,
        items=[],
        global_warnings=[PILLOW_MISSING],
    )
