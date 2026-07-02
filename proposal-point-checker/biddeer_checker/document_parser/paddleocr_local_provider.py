"""Local-only PaddleOCR implementation of the OCR provider boundary."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import math
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from PIL import Image

from biddeer_checker.document_parser.local_ocr_provider import (
    LocalOcrProviderResult,
    LocalOcrRequest,
)
from biddeer_checker.document_parser.ocr_result_artifact import (
    BOX_OR_POLYGON_NOT_OBSERVED,
    CONFIDENCE_NOT_OBSERVED,
    OcrArtifactStatus,
    OcrEngineInfo,
    OcrGeometry,
    OcrItem,
    OcrRuntimeInfo,
)


DEFAULT_DET_MODEL = "PP-OCRv6_tiny_det"
DEFAULT_REC_MODEL = "PP-OCRv6_tiny_rec"


def _load_paddleocr_class():
    from paddleocr import PaddleOCR

    return PaddleOCR


def _package_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def _result_payload(result: Any) -> Mapping[str, Any]:
    if isinstance(result, Mapping):
        return result
    candidate = getattr(result, "json", None)
    if callable(candidate):
        candidate = candidate()
    if isinstance(candidate, str):
        candidate = json.loads(candidate)
    if isinstance(candidate, Mapping):
        return candidate
    try:
        return dict(result)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"Unsupported PaddleOCR result type: {type(result).__name__}"
        ) from exc


def _result_body(result: Any) -> Mapping[str, Any]:
    payload = _result_payload(result)
    body = payload.get("res", payload)
    if not isinstance(body, Mapping):
        raise TypeError("PaddleOCR result payload does not contain a mapping")
    return body


def _provider_list(value: Any) -> list[Any]:
    if value is None:
        return []
    converter = getattr(value, "tolist", None)
    if callable(converter):
        value = converter()
    if isinstance(value, str):
        return [value]
    return list(value)


def _confidence_at(scores: list[Any], index: int) -> float | None:
    if index >= len(scores) or scores[index] is None:
        return None
    try:
        confidence = float(scores[index])
    except (TypeError, ValueError):
        return None
    return confidence if math.isfinite(confidence) else None


def _geometry_at(
    polygons: list[Any],
    index: int,
    *,
    image_width: int,
    image_height: int,
) -> OcrGeometry | None:
    if index >= len(polygons) or polygons[index] is None:
        return None
    try:
        points = tuple(
            (float(point[0]), float(point[1])) for point in polygons[index]
        )
        if len(points) != 4:
            return None
        return OcrGeometry(
            points=points,
            source_image_width=image_width,
            source_image_height=image_height,
        )
    except (IndexError, TypeError, ValueError):
        return None


class PaddleOcrLocalProvider:
    """Run PaddleOCR locally without importing it until recognition is used."""

    def __init__(
        self,
        *,
        device: str = "cpu",
        det_model: str = DEFAULT_DET_MODEL,
        rec_model: str = DEFAULT_REC_MODEL,
        language: str = "ch",
    ) -> None:
        self.device = device
        self.det_model = det_model
        self.rec_model = rec_model
        self.language = language
        self._engine: Any = None

    @property
    def engine_initialized(self) -> bool:
        return self._engine is not None

    def is_available(self) -> bool:
        try:
            return importlib.util.find_spec("paddleocr") is not None
        except (ImportError, ValueError):
            return False

    def _configuration(self) -> dict[str, Any]:
        return {
            "device": self.device,
            "text_detection_model_name": self.det_model,
            "text_recognition_model_name": self.rec_model,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
            "enable_mkldnn": False,
        }

    def _get_engine(self):
        if self._engine is None:
            paddleocr_class = _load_paddleocr_class()
            self._engine = paddleocr_class(**self._configuration())
        return self._engine

    def _engine_info(self) -> OcrEngineInfo:
        model_set = (
            "PP-OCRv6_tiny"
            if self.det_model == DEFAULT_DET_MODEL
            and self.rec_model == DEFAULT_REC_MODEL
            else None
        )
        return OcrEngineInfo(
            engine_name="paddleocr",
            engine_version=_package_version("paddleocr"),
            runtime_name="paddlepaddle",
            runtime_version=_package_version("paddlepaddle"),
            model_set=model_set,
            det_model=self.det_model,
            rec_model=self.rec_model,
            language_config=self.language,
            device=self.device,
            engine_config={
                "enable_mkldnn": False,
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": False,
            },
        )

    @staticmethod
    def _validated_image_path(request: LocalOcrRequest) -> Path:
        workspace = request.task_workspace.resolve()
        image_path = request.source_image_path.resolve()
        try:
            image_path.relative_to(workspace)
        except ValueError as exc:
            raise ValueError("OCR source image must remain beneath the workspace") from exc
        if not image_path.is_file():
            raise FileNotFoundError("OCR source image is not available")
        return image_path

    def recognize(self, request: LocalOcrRequest) -> LocalOcrProviderResult:
        started = time.perf_counter()
        image_path = self._validated_image_path(request)
        with Image.open(image_path) as image:
            image_width, image_height = image.size

        predictions = list(self._get_engine().predict(str(image_path)))
        bodies = [_result_body(prediction) for prediction in predictions]
        body = bodies[0] if bodies else {}
        texts = _provider_list(body.get("rec_texts"))
        scores = _provider_list(body.get("rec_scores"))
        polygons = _provider_list(body.get("rec_polys"))
        if not polygons:
            polygons = _provider_list(body.get("dt_polys"))

        items = []
        for index, raw_text in enumerate(texts):
            text = "" if raw_text is None else str(raw_text)
            items.append(
                OcrItem(
                    item_id=f"ocr-line-{index + 1:04d}",
                    text=text,
                    order=index + 1,
                    confidence=_confidence_at(scores, index),
                    geometry=_geometry_at(
                        polygons,
                        index,
                        image_width=image_width,
                        image_height=image_height,
                    ),
                )
            )

        warnings = []
        if items and any(item.confidence is None for item in items):
            warnings.append(CONFIDENCE_NOT_OBSERVED)
        if items and any(item.geometry is None for item in items):
            warnings.append(BOX_OR_POLYGON_NOT_OBSERVED)
        status = (
            OcrArtifactStatus.RECOGNIZED
            if any(item.text.strip() for item in items)
            else OcrArtifactStatus.EMPTY
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return LocalOcrProviderResult(
            status=status,
            engine=self._engine_info(),
            items=tuple(items),
            runtime=OcrRuntimeInfo(elapsed_ms=elapsed_ms),
            warnings=tuple(warnings),
        )
