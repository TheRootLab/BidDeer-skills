import importlib
import sys

from PIL import Image

from biddeer_checker.document_parser import paddleocr_local_provider as provider_module
from biddeer_checker.document_parser.local_ocr_provider import LocalOcrRequest
from biddeer_checker.document_parser.ocr_result_artifact import (
    BOX_OR_POLYGON_NOT_OBSERVED,
    CONFIDENCE_NOT_OBSERVED,
    OcrArtifactSource,
    OcrArtifactStatus,
)
from biddeer_checker.document_parser.paddleocr_local_provider import (
    DEFAULT_DET_MODEL,
    DEFAULT_REC_MODEL,
    PaddleOcrLocalProvider,
)


def _request(tmp_path, image_name="img_0001_01.png"):
    image_path = tmp_path / "images" / image_name
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (320, 120), "white").save(image_path)
    source = OcrArtifactSource(
        image_evidence_manifest_version="image-evidence-v0.1",
        image_id=image_path.stem,
        trace_id=f"trace-{image_path.stem}",
        source_doc_name="synthetic-proposal.pdf",
        source_page_num=1,
        related_check_item_id="CHECK-001",
        source_image_path=f"images/{image_name}",
        extraction_mode="targeted",
    )
    return LocalOcrRequest(
        task_workspace=tmp_path,
        source=source,
        source_image_path=image_path,
    )


def test_importing_provider_module_does_not_import_paddleocr():
    sys.modules.pop("paddleocr", None)

    importlib.reload(provider_module)

    assert "paddleocr" not in sys.modules


def test_availability_check_is_lazy(monkeypatch):
    provider = PaddleOcrLocalProvider()
    initialized = []
    monkeypatch.setattr(
        provider_module.importlib.util,
        "find_spec",
        lambda package: object() if package == "paddleocr" else None,
    )
    monkeypatch.setattr(
        provider_module,
        "_load_paddleocr_class",
        lambda: initialized.append(True),
    )

    assert provider.is_available() is True
    assert initialized == []
    assert provider.engine_initialized is False


def test_missing_paddleocr_is_reported_without_import(monkeypatch):
    provider = PaddleOcrLocalProvider()
    monkeypatch.setattr(
        provider_module.importlib.util,
        "find_spec",
        lambda _package: None,
    )

    assert provider.is_available() is False
    assert provider.engine_initialized is False


def test_mocked_output_normalizes_text_confidence_and_polygon(
    tmp_path,
    monkeypatch,
    caplog,
):
    constructor_calls = []

    class FakePaddleOCR:
        def __init__(self, **configuration):
            constructor_calls.append(configuration)

        def predict(self, _image_path):
            return [
                {
                    "res": {
                        "rec_texts": ["合成营业执照", "SYNTH-2026-001"],
                        "rec_scores": [0.98, 0.91],
                        "rec_polys": [
                            [[10, 10], [200, 10], [200, 40], [10, 40]],
                            [[10, 50], [220, 50], [220, 80], [10, 80]],
                        ],
                    }
                }
            ]

    monkeypatch.setattr(
        provider_module,
        "_load_paddleocr_class",
        lambda: FakePaddleOCR,
    )
    monkeypatch.setattr(
        provider_module,
        "_package_version",
        lambda package: {
            "paddleocr": "3.7.0",
            "paddlepaddle": "3.3.1",
        }.get(package),
    )
    provider = PaddleOcrLocalProvider(
        device="cpu",
        det_model="synthetic-det",
        rec_model="synthetic-rec",
        language="ch",
    )

    result = provider.recognize(_request(tmp_path))

    assert constructor_calls[0]["device"] == "cpu"
    assert constructor_calls[0]["text_detection_model_name"] == "synthetic-det"
    assert constructor_calls[0]["text_recognition_model_name"] == "synthetic-rec"
    assert result.status is OcrArtifactStatus.RECOGNIZED
    assert result.items[0].text == "合成营业执照"
    assert result.items[0].confidence == 0.98
    assert result.items[0].geometry.points == (
        (10.0, 10.0),
        (200.0, 10.0),
        (200.0, 40.0),
        (10.0, 40.0),
    )
    assert result.items[0].geometry.source_image_width == 320
    assert result.items[0].geometry.source_image_height == 120
    assert result.warnings == ()
    assert "合成营业执照" not in caplog.text


def test_missing_confidence_and_geometry_emit_warnings(tmp_path, monkeypatch):
    class FakePaddleOCR:
        def __init__(self, **_configuration):
            pass

        def predict(self, _image_path):
            return [{"res": {"rec_texts": ["synthetic text"]}}]

    monkeypatch.setattr(
        provider_module,
        "_load_paddleocr_class",
        lambda: FakePaddleOCR,
    )

    result = PaddleOcrLocalProvider().recognize(_request(tmp_path))

    assert result.items[0].confidence is None
    assert result.items[0].geometry is None
    assert result.warnings == (
        CONFIDENCE_NOT_OBSERVED,
        BOX_OR_POLYGON_NOT_OBSERVED,
    )


def test_defaults_use_ppocrv6_tiny_cpu_configuration():
    provider = PaddleOcrLocalProvider()

    assert provider.device == "cpu"
    assert provider.det_model == DEFAULT_DET_MODEL == "PP-OCRv6_tiny_det"
    assert provider.rec_model == DEFAULT_REC_MODEL == "PP-OCRv6_tiny_rec"
