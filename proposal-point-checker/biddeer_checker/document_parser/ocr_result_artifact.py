import json
import math
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


OCR_CONTRACT_VERSION = "paddleocr-result-v0.1"
OCR_ARTIFACT_TYPE = "local-ocr-result"
IMAGE_EVIDENCE_MANIFEST_VERSION = "image-evidence-v0.1"

MANUAL_REVIEW_REQUIRED_EMPTY_OCR = "MANUAL_REVIEW_REQUIRED_EMPTY_OCR"
CONFIDENCE_NOT_OBSERVED = "CONFIDENCE_NOT_OBSERVED"
BOX_OR_POLYGON_NOT_OBSERVED = "BOX_OR_POLYGON_NOT_OBSERVED"
OCR_RUNTIME_ERROR = "OCR_RUNTIME_ERROR"
OCR_PARTIAL_OUTPUT = "OCR_PARTIAL_OUTPUT"
OCR_PROVIDER_UNAVAILABLE = "OCR_PROVIDER_UNAVAILABLE"
MODEL_ARTIFACT_MISSING = "MODEL_ARTIFACT_MISSING"
MODEL_SOURCE_CONNECTIVITY_CHECK_REQUIRED = (
    "MODEL_SOURCE_CONNECTIVITY_CHECK_REQUIRED"
)
UNSUPPORTED_IMAGE_FORMAT = "UNSUPPORTED_IMAGE_FORMAT"
LOW_TEXT_QUALITY_OBSERVED = "LOW_TEXT_QUALITY_OBSERVED"

OCR_ARTIFACT_WARNINGS = (
    MANUAL_REVIEW_REQUIRED_EMPTY_OCR,
    CONFIDENCE_NOT_OBSERVED,
    BOX_OR_POLYGON_NOT_OBSERVED,
    OCR_RUNTIME_ERROR,
    OCR_PARTIAL_OUTPUT,
    OCR_PROVIDER_UNAVAILABLE,
    MODEL_ARTIFACT_MISSING,
    MODEL_SOURCE_CONNECTIVITY_CHECK_REQUIRED,
    UNSUPPORTED_IMAGE_FORMAT,
    LOW_TEXT_QUALITY_OBSERVED,
)
_WARNING_ORDER = {
    warning: index for index, warning in enumerate(OCR_ARTIFACT_WARNINGS)
}
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_OCR_ITEM_IDENTIFIER = re.compile(r"^ocr-line-[0-9]{4,}$")
_ALLOWED_EXTRACTION_MODES = {"targeted", "exhaustive_export"}


class OcrArtifactStatus(str, Enum):
    RECOGNIZED = "recognized"
    PARTIAL = "partial"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_identifier(value: str, field_name: str) -> str:
    _require_string(value, field_name)
    if (
        value in {".", ".."}
        or "/" in value
        or "\\" in value
        or not _SAFE_IDENTIFIER.fullmatch(value)
    ):
        raise ValueError(
            f"{field_name} must be a safe synthetic identifier without path separators"
        )
    return value


def _normalize_warnings(warnings: Iterable[str]) -> tuple[str, ...]:
    unique = set(warnings)
    unknown = unique.difference(_WARNING_ORDER)
    if unknown:
        raise ValueError(
            "Unsupported OCR artifact warning code(s): "
            + ", ".join(sorted(unknown))
        )
    return tuple(sorted(unique, key=_WARNING_ORDER.__getitem__))


def _relative_workspace_path(
    task_workspace: Path | str,
    relative_path: str,
    field_name: str,
) -> str:
    workspace = Path(task_workspace).resolve()
    path_value = _require_string(relative_path, field_name)
    if "\\" in path_value:
        raise ValueError(f"{field_name} must use a task-workspace-relative path")

    source_path = Path(path_value)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise ValueError(f"{field_name} must remain beneath the task workspace")

    resolved = (workspace / source_path).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must remain beneath the task workspace"
        ) from exc

    if resolved == workspace:
        raise ValueError(f"{field_name} must identify a file beneath the workspace")
    return source_path.as_posix()


@dataclass(frozen=True)
class OcrArtifactSource:
    image_evidence_manifest_version: str
    image_id: str
    trace_id: str
    source_doc_name: str
    source_page_num: int
    related_check_item_id: str
    source_image_path: str
    extraction_mode: str
    recognition_method: str = "local_ocr"

    def __post_init__(self) -> None:
        if self.image_evidence_manifest_version != IMAGE_EVIDENCE_MANIFEST_VERSION:
            raise ValueError(
                "imageEvidenceManifestVersion must be image-evidence-v0.1"
            )
        _validate_identifier(self.image_id, "imageId")
        _require_string(self.trace_id, "traceId")
        _require_string(self.source_doc_name, "sourceDocName")
        if "/" in self.source_doc_name or "\\" in self.source_doc_name:
            raise ValueError("sourceDocName must be a filename, not a path")
        if not isinstance(self.source_page_num, int) or self.source_page_num < 1:
            raise ValueError("sourcePageNum must be a positive integer")
        _require_string(self.related_check_item_id, "relatedCheckItemId")
        if self.extraction_mode not in _ALLOWED_EXTRACTION_MODES:
            raise ValueError(
                "extractionMode must be targeted or exhaustive_export"
            )
        if self.recognition_method != "local_ocr":
            raise ValueError("recognitionMethod must be local_ocr")
        source_image_path = _require_string(
            self.source_image_path,
            "sourceImagePath",
        )
        parsed_source_path = Path(source_image_path)
        if (
            "\\" in source_image_path
            or parsed_source_path.is_absolute()
            or ".." in parsed_source_path.parts
            or parsed_source_path == Path(".")
        ):
            raise ValueError(
                "sourceImagePath must be a task-workspace-relative file path"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "imageEvidenceManifestVersion": self.image_evidence_manifest_version,
            "imageId": self.image_id,
            "traceId": self.trace_id,
            "sourceDocName": self.source_doc_name,
            "sourcePageNum": self.source_page_num,
            "relatedCheckItemId": self.related_check_item_id,
            "sourceImagePath": self.source_image_path,
            "extractionMode": self.extraction_mode,
            "recognitionMethod": self.recognition_method,
        }


@dataclass(frozen=True)
class OcrEngineInfo:
    engine_name: str
    engine_version: Optional[str] = None
    runtime_name: Optional[str] = None
    runtime_version: Optional[str] = None
    model_set: Optional[str] = None
    det_model: Optional[str] = None
    rec_model: Optional[str] = None
    language_config: Optional[str] = None
    device: Optional[str] = None
    engine_config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_string(self.engine_name, "engineName")

    def to_dict(self) -> dict[str, Any]:
        fields = {
            "engineName": self.engine_name,
            "engineVersion": self.engine_version,
            "runtimeName": self.runtime_name,
            "runtimeVersion": self.runtime_version,
            "modelSet": self.model_set,
            "detModel": self.det_model,
            "recModel": self.rec_model,
            "languageConfig": self.language_config,
            "device": self.device,
        }
        result = {key: value for key, value in fields.items() if value is not None}
        if self.engine_config:
            result["engineConfig"] = dict(self.engine_config)
        return result


@dataclass(frozen=True)
class OcrGeometry:
    points: Sequence[Sequence[float]]
    source_image_width: int
    source_image_height: int
    geometry_type: str = "polygon"
    coordinate_space: str = "image_pixels"

    def __post_init__(self) -> None:
        if self.geometry_type != "polygon":
            raise ValueError("OCR geometry type must be polygon")
        if self.coordinate_space != "image_pixels":
            raise ValueError("OCR geometry coordinate space must be image_pixels")
        if len(self.points) != 4:
            raise ValueError("OCR polygon must contain exactly four points")
        for point in self.points:
            if len(point) != 2 or not all(
                isinstance(value, (int, float)) and math.isfinite(value)
                for value in point
            ):
                raise ValueError(
                    "Each OCR polygon point must contain finite x/y values"
                )
        if (
            not isinstance(self.source_image_width, int)
            or self.source_image_width < 1
            or not isinstance(self.source_image_height, int)
            or self.source_image_height < 1
        ):
            raise ValueError("OCR source image dimensions must be positive integers")

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.geometry_type,
            "points": [list(point) for point in self.points],
            "coordinateSpace": self.coordinate_space,
            "sourceImageWidth": self.source_image_width,
            "sourceImageHeight": self.source_image_height,
        }


@dataclass(frozen=True)
class OcrItem:
    item_id: str
    text: str
    order: int
    confidence: Optional[float] = None
    geometry: Optional[OcrGeometry] = None
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not _OCR_ITEM_IDENTIFIER.fullmatch(
            self.item_id
        ):
            raise ValueError(
                "itemId must use the synthetic artifact-local form ocr-line-NNNN"
            )
        if not isinstance(self.text, str):
            raise ValueError("OCR item text must be a string")
        if not isinstance(self.order, int) or self.order < 1:
            raise ValueError("OCR item order must be a positive integer")
        if self.confidence is not None and (
            not isinstance(self.confidence, (int, float))
            or not math.isfinite(self.confidence)
        ):
            raise ValueError("OCR confidence must be a finite number when observed")
        _normalize_warnings(self.warnings)

    def normalized_warnings(self) -> tuple[str, ...]:
        warnings = list(self.warnings)
        if self.confidence is None:
            warnings.append(CONFIDENCE_NOT_OBSERVED)
        if self.geometry is None:
            warnings.append(BOX_OR_POLYGON_NOT_OBSERVED)
        return _normalize_warnings(warnings)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "itemId": self.item_id,
            "text": self.text,
            "order": self.order,
            "warnings": list(self.normalized_warnings()),
        }
        if self.confidence is not None:
            result["confidence"] = self.confidence
        if self.geometry is not None:
            result["geometry"] = self.geometry.to_dict()
        return result


@dataclass(frozen=True)
class OcrRuntimeInfo:
    elapsed_ms: Optional[int] = None
    peak_resident_memory_mib: Optional[float] = None

    def __post_init__(self) -> None:
        if self.elapsed_ms is not None and (
            not isinstance(self.elapsed_ms, int) or self.elapsed_ms < 0
        ):
            raise ValueError("elapsedMs must be a non-negative integer")
        if self.peak_resident_memory_mib is not None and (
            not isinstance(self.peak_resident_memory_mib, (int, float))
            or not math.isfinite(self.peak_resident_memory_mib)
            or self.peak_resident_memory_mib < 0
        ):
            raise ValueError(
                "peakResidentMemoryMiB must be a non-negative finite number"
            )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.elapsed_ms is not None:
            result["elapsedMs"] = self.elapsed_ms
        if self.peak_resident_memory_mib is not None:
            result["peakResidentMemoryMiB"] = self.peak_resident_memory_mib
        return result


@dataclass(frozen=True)
class OcrPrivacyInfo:
    local_only: bool = True
    uploaded: bool = False
    logs_contain_full_text: bool = False

    def __post_init__(self) -> None:
        if (
            self.local_only is not True
            or self.uploaded is not False
            or self.logs_contain_full_text is not False
        ):
            raise ValueError(
                "OCR artifact privacy must enforce local-only, no-upload, "
                "and no-full-text normal logs"
            )

    def to_dict(self) -> dict[str, bool]:
        return {
            "localOnly": self.local_only,
            "uploaded": self.uploaded,
            "logsContainFullText": self.logs_contain_full_text,
        }


@dataclass(frozen=True)
class OcrResultArtifact:
    source: OcrArtifactSource
    status: OcrArtifactStatus
    items: Sequence[OcrItem] = field(default_factory=tuple)
    warnings: Sequence[str] = field(default_factory=tuple)
    engine: Optional[OcrEngineInfo] = None
    runtime: OcrRuntimeInfo = field(default_factory=OcrRuntimeInfo)
    privacy: OcrPrivacyInfo = field(default_factory=OcrPrivacyInfo)

    def __post_init__(self) -> None:
        _normalize_warnings(self.warnings)

    @property
    def text(self) -> str:
        ordered = sorted(self.items, key=lambda item: item.order)
        return "\n".join(item.text for item in ordered if item.text.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "contractVersion": OCR_CONTRACT_VERSION,
            "artifactType": OCR_ARTIFACT_TYPE,
            "source": self.source.to_dict(),
            "engine": self.engine.to_dict() if self.engine is not None else {},
            "result": {
                "status": self.status.value,
                "text": self.text,
                "items": [
                    item.to_dict()
                    for item in sorted(self.items, key=lambda item: item.order)
                ],
                "warnings": list(_normalize_warnings(self.warnings)),
            },
            "runtime": self.runtime.to_dict(),
            "privacy": self.privacy.to_dict(),
        }


def build_ocr_source_from_image_evidence_item(
    image_evidence_item: Mapping[str, Any],
    *,
    extraction_mode: str,
    task_workspace: Path | str,
) -> OcrArtifactSource:
    manifest_version = image_evidence_item.get("manifestVersion")
    if manifest_version != IMAGE_EVIDENCE_MANIFEST_VERSION:
        raise ValueError(
            "imageEvidenceManifestVersion must originate from image-evidence-v0.1"
        )
    if image_evidence_item.get("extractionMethod") != "embedded_image":
        raise ValueError(
            "extractionMethod must be embedded_image for image-evidence-v0.1"
        )

    source_image_path = _relative_workspace_path(
        task_workspace,
        image_evidence_item.get("imagePath"),
        "sourceImagePath",
    )
    return OcrArtifactSource(
        image_evidence_manifest_version=manifest_version,
        image_id=image_evidence_item.get("imageId"),
        trace_id=image_evidence_item.get("traceId"),
        source_doc_name=image_evidence_item.get("sourceDocName"),
        source_page_num=image_evidence_item.get("sourcePageNum"),
        related_check_item_id=image_evidence_item.get("relatedCheckItemId"),
        source_image_path=source_image_path,
        extraction_mode=extraction_mode,
    )


def build_ocr_result_artifact(
    *,
    source: OcrArtifactSource,
    engine: OcrEngineInfo,
    items: Sequence[OcrItem],
    runtime: OcrRuntimeInfo,
    status: OcrArtifactStatus = OcrArtifactStatus.RECOGNIZED,
    warnings: Iterable[str] = (),
) -> OcrResultArtifact:
    if status in {OcrArtifactStatus.UNAVAILABLE, OcrArtifactStatus.ERROR}:
        raise ValueError("Use the unavailable/error artifact builders")

    ordered_items = tuple(sorted(items, key=lambda item: item.order))
    if len({item.order for item in ordered_items}) != len(ordered_items):
        raise ValueError("OCR item order values must be unique")

    combined_text = "\n".join(
        item.text for item in ordered_items if item.text.strip()
    )
    normalized = list(warnings)
    for item in ordered_items:
        normalized.extend(item.normalized_warnings())

    if not combined_text:
        status = OcrArtifactStatus.EMPTY
        normalized.append(MANUAL_REVIEW_REQUIRED_EMPTY_OCR)
    elif status is OcrArtifactStatus.EMPTY:
        raise ValueError("empty status cannot contain recognized text")
    elif status is OcrArtifactStatus.PARTIAL:
        normalized.append(OCR_PARTIAL_OUTPUT)

    return OcrResultArtifact(
        source=source,
        status=status,
        engine=engine,
        items=ordered_items,
        warnings=_normalize_warnings(normalized),
        runtime=runtime,
    )


def build_unavailable_ocr_artifact(
    source: OcrArtifactSource,
    *,
    warnings: Iterable[str] = (OCR_PROVIDER_UNAVAILABLE,),
    engine: Optional[OcrEngineInfo] = None,
) -> OcrResultArtifact:
    normalized = _normalize_warnings(warnings)
    if not normalized:
        normalized = (OCR_PROVIDER_UNAVAILABLE,)
    return OcrResultArtifact(
        source=source,
        status=OcrArtifactStatus.UNAVAILABLE,
        engine=engine,
        warnings=normalized,
    )


def build_error_ocr_artifact(
    source: OcrArtifactSource,
    *,
    error: Optional[BaseException] = None,
    warnings: Iterable[str] = (OCR_RUNTIME_ERROR,),
    engine: Optional[OcrEngineInfo] = None,
    runtime: Optional[OcrRuntimeInfo] = None,
) -> OcrResultArtifact:
    del error
    normalized = _normalize_warnings(warnings)
    if OCR_RUNTIME_ERROR not in normalized:
        normalized = _normalize_warnings((*normalized, OCR_RUNTIME_ERROR))
    return OcrResultArtifact(
        source=source,
        status=OcrArtifactStatus.ERROR,
        engine=engine,
        warnings=normalized,
        runtime=runtime or OcrRuntimeInfo(),
    )


def ocr_result_path_for_image(
    task_workspace: Path | str,
    image_id: str,
) -> Path:
    safe_image_id = _validate_identifier(image_id, "imageId")
    workspace = Path(task_workspace).resolve()
    result_path = workspace / "ocr_results" / f"{safe_image_id}.paddleocr.json"
    try:
        result_path.resolve().relative_to(workspace)
    except ValueError as exc:
        raise ValueError(
            "OCR artifact path must remain beneath the task workspace"
        ) from exc
    return result_path


def write_ocr_result_artifact(
    task_workspace: Path | str,
    artifact: OcrResultArtifact,
) -> Path:
    artifact_path = ocr_result_path_for_image(
        task_workspace,
        artifact.source.image_id,
    )
    artifact_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    serialized = (
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(artifact_path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as artifact_file:
            artifact_file.write(serialized)
            artifact_file.flush()
            os.fsync(artifact_file.fileno())
    except BaseException:
        artifact_path.unlink(missing_ok=True)
        raise
    return artifact_path
