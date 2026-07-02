"""Local OCR review workflow for extracted PDF image evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from biddeer_checker.document_parser.local_ocr_provider import (
    LocalOcrExecution,
    LocalOcrProvider,
    run_local_ocr_provider,
)
from biddeer_checker.document_parser.ocr_result_artifact import (
    IMAGE_EVIDENCE_MANIFEST_VERSION,
    OcrArtifactStatus,
)


DEFAULT_DET_MODEL = "PP-OCRv6_tiny_det"
DEFAULT_REC_MODEL = "PP-OCRv6_tiny_rec"
DEFAULT_REPORT_NAME = "image_ocr_review_report.md"
_EXCERPT_LIMIT = 800


@dataclass(frozen=True)
class ImageOcrReviewWorkflowResult:
    manifest_path: Path
    report_path: Path
    selected_count: int
    executions: Sequence[LocalOcrExecution]


def _workspace_file(
    workspace: Path,
    path: Path | str,
    *,
    field_name: str,
) -> Path:
    candidate = Path(path)
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (workspace / candidate).resolve()
    )
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"{field_name} must remain beneath the workspace") from exc
    if resolved == workspace:
        raise ValueError(f"{field_name} must identify a file")
    return resolved


def _load_manifest(manifest_path: Path) -> Mapping[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("image evidence manifest must be a JSON object")
    if payload.get("manifestVersion") != IMAGE_EVIDENCE_MANIFEST_VERSION:
        raise ValueError("manifestVersion must be image-evidence-v0.1")
    if payload.get("extractionMode") not in {"targeted", "exhaustive_export"}:
        raise ValueError("extractionMode must be targeted or exhaustive_export")
    if not isinstance(payload.get("items"), list):
        raise ValueError("image evidence manifest items must be an array")
    return payload


def _select_image_items(
    manifest: Mapping[str, Any],
    workspace: Path,
) -> list[Mapping[str, Any]]:
    selected = []
    for item in manifest["items"]:
        if not isinstance(item, Mapping):
            continue
        if item.get("extractionMethod") != "embedded_image":
            continue
        image_path = item.get("imagePath")
        if not isinstance(image_path, str) or not image_path.strip():
            continue
        try:
            local_image = _workspace_file(
                workspace,
                image_path,
                field_name="imagePath",
            )
        except ValueError:
            continue
        if not local_image.is_file():
            continue
        selected.append(item)
    return sorted(
        selected,
        key=lambda item: (
            item.get("sourcePageNum", 0),
            item.get("relatedCheckItemId", ""),
            item.get("imageId", ""),
        ),
    )


def _code_fence(text: str) -> str:
    longest_run = 0
    current_run = 0
    for character in text:
        if character == "`":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    return "`" * max(3, longest_run + 1)


def _text_excerpt(text: str) -> str:
    if len(text) <= _EXCERPT_LIMIT:
        return text
    return text[:_EXCERPT_LIMIT].rstrip() + "\n[excerpt truncated]"


def _render_report(executions: Sequence[LocalOcrExecution]) -> str:
    lines = [
        "# Image OCR Review Report",
        "",
        (
            "This report contains supplemental local OCR observations for "
            "manual image review."
        ),
        "",
    ]
    if executions and all(
        execution.artifact.status is OcrArtifactStatus.UNAVAILABLE
        for execution in executions
    ):
        lines.extend(
            [
                (
                    "PaddleOCR is unavailable. Install the optional local OCR "
                    "dependencies and keep the source images available for "
                    "manual review."
                ),
                "",
            ]
        )

    if not executions:
        lines.extend(
            [
                "No extracted embedded-image artifacts were selected.",
                "",
            ]
        )

    for execution in executions:
        artifact = execution.artifact
        source = artifact.source
        warnings = ", ".join(artifact.warnings) or "none"
        lines.extend(
            [
                (
                    f"## Page {source.source_page_num} / "
                    f"{source.related_check_item_id} / {source.image_id}"
                ),
                "",
                f"- Image: `{source.source_image_path}`",
                (
                    "- OCR artifact: "
                    f"`ocr_results/{execution.artifact_path.name}`"
                ),
                f"- OCR status: `{artifact.status.value}`",
                "- OCR text excerpt:",
                "",
            ]
        )
        excerpt = _text_excerpt(artifact.text)
        if excerpt:
            fence = _code_fence(excerpt)
            lines.extend([f"{fence}text", excerpt, fence, ""])
        else:
            lines.extend(["```text", "[no recognized text]", "```", ""])
        lines.extend(
            [
                f"- Warnings: {warnings}",
                (
                    "- Manual review note: OCR text is supplemental. Please "
                    "manually verify whether this image corresponds to the "
                    "required document."
                ),
                "",
            ]
        )
    return "\n".join(lines)


def run_image_ocr_review_workflow(
    *,
    workspace: Path | str,
    manifest_path: Path | str,
    output_path: Path | str,
    provider: LocalOcrProvider,
) -> ImageOcrReviewWorkflowResult:
    task_workspace = Path(workspace).resolve()
    if not task_workspace.is_dir():
        raise ValueError("workspace must be an existing directory")
    source_manifest_path = _workspace_file(
        task_workspace,
        manifest_path,
        field_name="manifest",
    )
    report_path = _workspace_file(
        task_workspace,
        output_path,
        field_name="output",
    )
    if report_path == source_manifest_path:
        raise ValueError("output must not overwrite manifest")
    manifest = _load_manifest(source_manifest_path)
    selected_items = _select_image_items(manifest, task_workspace)

    executions = tuple(
        run_local_ocr_provider(
            provider=provider,
            task_workspace=task_workspace,
            image_evidence_item=item,
            extraction_mode=manifest["extractionMode"],
        )
        for item in selected_items
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(executions), encoding="utf-8")
    return ImageOcrReviewWorkflowResult(
        manifest_path=source_manifest_path,
        report_path=report_path,
        selected_count=len(selected_items),
        executions=executions,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local PaddleOCR on extracted PDF image artifacts."
    )
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--det-model", default=DEFAULT_DET_MODEL)
    parser.add_argument("--rec-model", default=DEFAULT_REC_MODEL)
    parser.add_argument("--lang", default="ch")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    from biddeer_checker.document_parser.paddleocr_local_provider import (
        PaddleOcrLocalProvider,
    )

    provider = PaddleOcrLocalProvider(
        device=args.device,
        det_model=args.det_model,
        rec_model=args.rec_model,
        language=args.lang,
    )
    result = run_image_ocr_review_workflow(
        workspace=args.workspace,
        manifest_path=args.manifest,
        output_path=args.out,
        provider=provider,
    )
    statuses = [execution.artifact.status for execution in result.executions]
    print(
        f"OCR review report written for {result.selected_count} image artifact(s): "
        f"{result.report_path}"
    )
    if any(status is OcrArtifactStatus.ERROR for status in statuses):
        return 1
    if any(status is OcrArtifactStatus.UNAVAILABLE for status in statuses):
        print(
            "Local PaddleOCR is unavailable. Install requirements-ocr.txt and "
            "review unavailable images manually."
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
