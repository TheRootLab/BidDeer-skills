from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from biddeer_checker.document_parser.ocr_result_artifact import (
    OCR_PROVIDER_UNAVAILABLE,
    OCR_RUNTIME_ERROR,
    OcrArtifactSource,
    OcrArtifactStatus,
    OcrEngineInfo,
    OcrItem,
    OcrResultArtifact,
    OcrRuntimeInfo,
    build_error_ocr_artifact,
    build_ocr_result_artifact,
    build_ocr_source_from_image_evidence_item,
    build_unavailable_ocr_artifact,
    write_ocr_result_artifact,
)


@dataclass(frozen=True)
class LocalOcrRequest:
    task_workspace: Path
    source: OcrArtifactSource
    source_image_path: Path


@dataclass(frozen=True)
class LocalOcrProviderResult:
    status: OcrArtifactStatus
    engine: Optional[OcrEngineInfo] = None
    items: Sequence[OcrItem] = field(default_factory=tuple)
    runtime: OcrRuntimeInfo = field(default_factory=OcrRuntimeInfo)
    warnings: Sequence[str] = field(default_factory=tuple)


@runtime_checkable
class LocalOcrProvider(Protocol):
    def is_available(self) -> bool:
        """Return whether this explicitly configured local provider is usable."""

    def recognize(self, request: LocalOcrRequest) -> LocalOcrProviderResult:
        """Recognize one selected local image without uploading its content."""


@dataclass(frozen=True)
class LocalOcrExecution:
    artifact: OcrResultArtifact
    artifact_path: Path


def _artifact_from_provider_result(
    source: OcrArtifactSource,
    result: LocalOcrProviderResult,
) -> OcrResultArtifact:
    if result.status is OcrArtifactStatus.UNAVAILABLE:
        return build_unavailable_ocr_artifact(
            source,
            warnings=result.warnings or (OCR_PROVIDER_UNAVAILABLE,),
            engine=result.engine,
        )
    if result.status is OcrArtifactStatus.ERROR:
        return build_error_ocr_artifact(
            source,
            warnings=result.warnings or (OCR_RUNTIME_ERROR,),
            engine=result.engine,
            runtime=result.runtime,
        )
    if result.engine is None:
        raise ValueError(
            "Recognized, partial, or empty provider results require engine metadata"
        )
    return build_ocr_result_artifact(
        source=source,
        engine=result.engine,
        items=result.items,
        runtime=result.runtime,
        status=result.status,
        warnings=result.warnings,
    )


def run_local_ocr_provider(
    *,
    provider: LocalOcrProvider,
    task_workspace: Path | str,
    image_evidence_item: Mapping[str, Any],
    extraction_mode: str,
) -> LocalOcrExecution:
    workspace = Path(task_workspace).resolve()
    source = build_ocr_source_from_image_evidence_item(
        image_evidence_item,
        extraction_mode=extraction_mode,
        task_workspace=workspace,
    )
    request = LocalOcrRequest(
        task_workspace=workspace,
        source=source,
        source_image_path=(workspace / source.source_image_path).resolve(),
    )

    try:
        available = provider.is_available()
    except Exception:
        available = False

    if not available:
        artifact = build_unavailable_ocr_artifact(source)
    else:
        try:
            provider_result = provider.recognize(request)
            artifact = _artifact_from_provider_result(source, provider_result)
        except Exception as error:
            artifact = build_error_ocr_artifact(source, error=error)

    artifact_path = write_ocr_result_artifact(workspace, artifact)
    return LocalOcrExecution(artifact=artifact, artifact_path=artifact_path)
