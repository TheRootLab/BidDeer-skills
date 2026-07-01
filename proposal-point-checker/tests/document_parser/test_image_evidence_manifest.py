import json
from pathlib import Path

from biddeer_checker.document_parser.image_evidence_manifest import (
    MANIFEST_VERSION,
    build_manifest,
    write_pillow_missing_manifest,
)
from biddeer_checker.document_parser.pdf_image_extractor import (
    CONSENT_REQUIRED,
    EXTRACTION_STATE_UNAVAILABLE,
    PILLOW_MISSING,
    ExtractedImage,
)


def _targeted_item() -> ExtractedImage:
    return ExtractedImage(
        sourcePageNum=3,
        imageIndex=1,
        imageId="img_0003_01_01",
        traceId="trace-test",
        imagePath="images/img_0003_01_01.png",
        imageSha256="abc123",
        imageWidth=20,
        imageHeight=20,
        imageFormat="PNG",
        recognitionState=CONSENT_REQUIRED,
        recognitionMethod="none",
        relatedCheckItemId="ITEM-003",
        nearbyText="retrieved evidence",
        nearbyTextScope="retrieval_context",
    )


def test_targeted_manifest_contains_association_and_relative_path():
    manifest = build_manifest(
        source_doc_name="proposal.pdf",
        extraction_mode="targeted",
        items=[_targeted_item()],
        global_warnings=[],
    )
    assert manifest["manifestVersion"] == MANIFEST_VERSION
    assert manifest["sourceDocName"] == "proposal.pdf"
    assert manifest["extractionMode"] == "targeted"
    item = manifest["items"][0]
    assert item["relatedCheckItemId"] == "ITEM-003"
    assert item["nearbyText"] == "retrieved evidence"
    assert item["nearbyTextScope"] == "retrieval_context"
    assert item["recognitionMethod"] == "none"
    assert not Path(item["imagePath"]).is_absolute()
    assert "/tmp/" not in json.dumps(manifest)


def test_missing_pillow_writes_unavailable_targeted_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "biddeer_checker.document_parser.image_evidence_manifest._get_pillow_version",
        lambda: None,
    )
    path = write_pillow_missing_manifest(
        workspace_dir=str(tmp_path),
        source_doc_name="proposal.pdf",
        extraction_mode="targeted",
    )
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    assert manifest["extractionMode"] == "targeted"
    assert manifest["extractionState"] == EXTRACTION_STATE_UNAVAILABLE
    assert manifest["warnings"] == [PILLOW_MISSING]
    assert manifest["imageRuntime"]["imageDependencyVersion"] is None
    assert manifest["items"] == []
