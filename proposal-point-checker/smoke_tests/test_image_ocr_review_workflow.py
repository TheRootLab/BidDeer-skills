import json
from copy import deepcopy

import pytest

from biddeer_checker.document_parser.image_ocr_review_workflow import (
    run_image_ocr_review_workflow,
)
from biddeer_checker.document_parser.local_ocr_provider import (
    LocalOcrProviderResult,
)
from biddeer_checker.document_parser.ocr_result_artifact import (
    OCR_PROVIDER_UNAVAILABLE,
    OCR_RUNTIME_ERROR,
    OcrArtifactStatus,
    OcrEngineInfo,
    OcrItem,
    OcrRuntimeInfo,
)


def _manifest_item(image_id, page_num, check_item_id, **overrides):
    item = {
        "manifestVersion": "image-evidence-v0.1",
        "sourceDocName": "synthetic-proposal.pdf",
        "sourcePageNum": page_num,
        "imageId": image_id,
        "imagePath": f"images/{image_id}.png",
        "imageSha256": f"synthetic-sha-{image_id}",
        "imageWidth": 100,
        "imageHeight": 50,
        "imageFormat": "PNG",
        "relatedCheckItemId": check_item_id,
        "nearbyText": "synthetic nearby text",
        "nearbyTextScope": "same_page",
        "extractionMethod": "embedded_image",
        "recognitionState": "CONSENT_REQUIRED",
        "recognitionMethod": "none",
        "warnings": [],
        "traceId": f"trace-{image_id}",
    }
    item.update(overrides)
    return item


def _write_manifest(workspace, items, extraction_mode="targeted"):
    payload = {
        "manifestVersion": "image-evidence-v0.1",
        "sourceDocName": "synthetic-proposal.pdf",
        "createdAt": "2026-07-02T00:00:00+00:00",
        "extractionMode": extraction_mode,
        "extractionState": "completed",
        "imageRuntime": {},
        "items": items,
        "warnings": [],
    }
    manifest_path = workspace / "image_evidence_manifest.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path, payload


def _write_selected_images(workspace, items):
    (workspace / "images").mkdir()
    for item in items:
        image_path = item.get("imagePath")
        if image_path:
            (workspace / image_path).write_bytes(b"synthetic-image-bytes")


def _engine():
    return OcrEngineInfo(
        engine_name="fake-local-ocr",
        engine_version="1.0",
        runtime_name="synthetic-runtime",
        runtime_version="1.0",
        model_set="synthetic",
        det_model="synthetic-det",
        rec_model="synthetic-rec",
        language_config="ch",
        device="cpu",
    )


class FakeWorkflowProvider:
    def __init__(self, *, unavailable=False, error_image_ids=()):
        self.unavailable = unavailable
        self.error_image_ids = set(error_image_ids)
        self.requests = []

    def is_available(self):
        return not self.unavailable

    def recognize(self, request):
        self.requests.append(request)
        image_id = request.source.image_id
        if image_id in self.error_image_ids:
            raise RuntimeError(f"synthetic provider error for {image_id}")
        return LocalOcrProviderResult(
            status=OcrArtifactStatus.RECOGNIZED,
            engine=_engine(),
            items=(
                OcrItem(
                    item_id="ocr-line-0001",
                    text=f"synthetic OCR text for {image_id}",
                    order=1,
                    confidence=0.91,
                ),
            ),
            runtime=OcrRuntimeInfo(elapsed_ms=3),
        )


def test_workflow_selects_local_embedded_images_and_writes_artifacts(tmp_path):
    selected = [
        _manifest_item("img_0002_01", 2, "CHECK-002"),
        _manifest_item("img_0001_01", 1, "CHECK-001"),
    ]
    ignored = [
        _manifest_item(
            "img_0003_01",
            3,
            "CHECK-003",
            extractionMethod="rendered_page",
        ),
        _manifest_item("img_0004_01", 4, "CHECK-004", imagePath=None),
    ]
    manifest_path, _payload = _write_manifest(tmp_path, [*selected, *ignored])
    _write_selected_images(tmp_path, selected)
    provider = FakeWorkflowProvider()

    result = run_image_ocr_review_workflow(
        workspace=tmp_path,
        manifest_path=manifest_path,
        output_path=tmp_path / "image_ocr_review_report.md",
        provider=provider,
    )

    assert [request.source.image_id for request in provider.requests] == [
        "img_0001_01",
        "img_0002_01",
    ]
    assert result.selected_count == 2
    assert (tmp_path / "ocr_results/img_0001_01.paddleocr.json").exists()
    assert (tmp_path / "ocr_results/img_0002_01.paddleocr.json").exists()


def test_workflow_continues_after_per_image_error(tmp_path):
    items = [
        _manifest_item("img_0001_01", 1, "CHECK-001"),
        _manifest_item("img_0002_01", 2, "CHECK-002"),
    ]
    manifest_path, _payload = _write_manifest(tmp_path, items)
    _write_selected_images(tmp_path, items)

    result = run_image_ocr_review_workflow(
        workspace=tmp_path,
        manifest_path=manifest_path,
        output_path=tmp_path / "image_ocr_review_report.md",
        provider=FakeWorkflowProvider(error_image_ids={"img_0001_01"}),
    )

    statuses = {
        execution.artifact.source.image_id: execution.artifact.status
        for execution in result.executions
    }
    assert statuses == {
        "img_0001_01": OcrArtifactStatus.ERROR,
        "img_0002_01": OcrArtifactStatus.RECOGNIZED,
    }
    error_payload = json.loads(
        (tmp_path / "ocr_results/img_0001_01.paddleocr.json").read_text(
            encoding="utf-8"
        )
    )
    assert error_payload["result"]["warnings"] == [OCR_RUNTIME_ERROR]


def test_unavailable_provider_writes_artifacts_and_manual_guidance(tmp_path):
    items = [_manifest_item("img_0001_01", 1, "CHECK-001")]
    manifest_path, _payload = _write_manifest(tmp_path, items)
    _write_selected_images(tmp_path, items)
    report_path = tmp_path / "image_ocr_review_report.md"

    result = run_image_ocr_review_workflow(
        workspace=tmp_path,
        manifest_path=manifest_path,
        output_path=report_path,
        provider=FakeWorkflowProvider(unavailable=True),
    )

    assert result.executions[0].artifact.status is OcrArtifactStatus.UNAVAILABLE
    assert result.executions[0].artifact.warnings == (OCR_PROVIDER_UNAVAILABLE,)
    report = report_path.read_text(encoding="utf-8")
    assert "optional local OCR dependencies" in report
    assert "manual review" in report


def test_report_contains_provenance_status_artifact_and_excerpt(tmp_path):
    item = _manifest_item("img_0012_01", 12, "CHECK-003")
    manifest_path, _payload = _write_manifest(tmp_path, [item])
    _write_selected_images(tmp_path, [item])
    report_path = tmp_path / "image_ocr_review_report.md"

    run_image_ocr_review_workflow(
        workspace=tmp_path,
        manifest_path=manifest_path,
        output_path=report_path,
        provider=FakeWorkflowProvider(),
    )

    report = report_path.read_text(encoding="utf-8")
    assert "## Page 12 / CHECK-003 / img_0012_01" in report
    assert "- Image: `images/img_0012_01.png`" in report
    assert "- OCR artifact: `ocr_results/img_0012_01.paddleocr.json`" in report
    assert "- OCR status: `recognized`" in report
    assert "synthetic OCR text for img_0012_01" in report
    assert "OCR text is supplemental" in report


def test_report_avoids_forbidden_conclusions(tmp_path):
    item = _manifest_item("img_0001_01", 1, "CHECK-001")
    manifest_path, _payload = _write_manifest(tmp_path, [item])
    _write_selected_images(tmp_path, [item])
    report_path = tmp_path / "image_ocr_review_report.md"

    run_image_ocr_review_workflow(
        workspace=tmp_path,
        manifest_path=manifest_path,
        output_path=report_path,
        provider=FakeWorkflowProvider(),
    )

    report = report_path.read_text(encoding="utf-8").lower()
    forbidden = (
        "bid passes",
        "bid fails",
        "bid rejection",
        "risk level",
        "certificate is valid",
        "seal is authentic",
        "signature is authentic",
        "automatically compliant",
    )
    assert all(phrase not in report for phrase in forbidden)


def test_workflow_does_not_mutate_manifest_or_log_full_text(tmp_path, caplog):
    item = _manifest_item("img_0001_01", 1, "CHECK-001")
    manifest_path, manifest_payload = _write_manifest(tmp_path, [item])
    original_bytes = manifest_path.read_bytes()
    original_payload = deepcopy(manifest_payload)
    _write_selected_images(tmp_path, [item])

    run_image_ocr_review_workflow(
        workspace=tmp_path,
        manifest_path=manifest_path,
        output_path=tmp_path / "image_ocr_review_report.md",
        provider=FakeWorkflowProvider(),
    )

    assert manifest_path.read_bytes() == original_bytes
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == original_payload
    assert "synthetic OCR text for img_0001_01" not in caplog.text


def test_workflow_rejects_output_that_would_overwrite_manifest(tmp_path):
    manifest_path, _payload = _write_manifest(tmp_path, [])

    with pytest.raises(ValueError, match="output must not overwrite manifest"):
        run_image_ocr_review_workflow(
            workspace=tmp_path,
            manifest_path=manifest_path,
            output_path=manifest_path,
            provider=FakeWorkflowProvider(),
        )
