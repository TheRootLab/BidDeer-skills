import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from biddeer_checker.checklist_model.models import ChecklistItem
from biddeer_checker.checklist_model.parser import CSVChecklistParser
from biddeer_checker.document_parser.models import ImageObject, UserFacingLocator
from biddeer_checker.document_parser.parser import DocxDocumentParser
from biddeer_checker.evidence_reasoning.models import (
    EvidenceStatus,
    JudgedEvidencePackage,
    ReasoningResult,
)
from biddeer_checker.evidence_retrieval.engine import retrieve_evidence
from biddeer_checker.evidence_retrieval.models import CandidateEvidence, EvidencePackage
from biddeer_checker.report_renderer.aggregator import ReportAggregator
from biddeer_checker.report_renderer.csv_renderer import CSVRenderer
from biddeer_checker.report_renderer.markdown_renderer import MarkdownRenderer


CANDIDATES_SCHEMA_VERSION = "proposal-point-checker.candidates.v0.1"
JUDGMENTS_SCHEMA_VERSION = "proposal-point-checker.judgments.v0.1"


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="biddeer_checker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    retrieve_parser = subparsers.add_parser(
        "retrieve",
        help="Parse CSV/DOCX and write candidate evidence JSON.",
    )
    retrieve_parser.add_argument("--csv", required=True)
    retrieve_parser.add_argument("--docx", required=True)
    retrieve_parser.add_argument("--out", required=True)
    retrieve_parser.set_defaults(handler=_run_retrieve)

    report_parser = subparsers.add_parser(
        "report",
        help="Render a human-review report from candidate evidence and external judgments.",
    )
    report_parser.add_argument("--candidates", required=True)
    report_parser.add_argument("--judgments", required=True)
    report_parser.add_argument("--out", required=True)
    report_parser.add_argument(
        "--format",
        choices=("markdown", "csv"),
        default="markdown",
    )
    report_parser.set_defaults(handler=_run_report)

    return parser


def _run_retrieve(args: argparse.Namespace) -> int:
    items, errors = CSVChecklistParser().parse(args.csv)
    if errors:
        raise ValueError(f"CSV checklist parse failed: {errors}")

    document = DocxDocumentParser().parse(args.docx)
    packages = retrieve_evidence(items, document)

    payload = {
        "schemaVersion": CANDIDATES_SCHEMA_VERSION,
        "packages": [_serialize_evidence_package(package) for package in packages],
    }
    _write_json(args.out, payload)
    return 0


def _run_report(args: argparse.Namespace) -> int:
    candidates_payload = _read_json(args.candidates)
    judgments_payload = _read_json(args.judgments)

    _require_schema_version(
        candidates_payload,
        CANDIDATES_SCHEMA_VERSION,
        "candidates",
    )
    _require_schema_version(
        judgments_payload,
        JUDGMENTS_SCHEMA_VERSION,
        "judgments",
    )

    packages = [
        _deserialize_evidence_package(package_data)
        for package_data in candidates_payload["packages"]
    ]
    judgments_by_item_id = _build_judgments_by_item_id(
        judgments_payload["judgments"],
        [package.item.itemId for package in packages],
    )

    judged_packages = []
    for package in packages:
        item_id = package.item.itemId
        judged_packages.append(
            JudgedEvidencePackage(
                package=package,
                result=judgments_by_item_id[item_id],
            )
        )

    report = ReportAggregator.aggregate(judged_packages)
    if args.format == "csv":
        rendered = CSVRenderer.render(report)
        with open(args.out, "w", encoding="utf-8-sig", newline="") as file:
            file.write(rendered)
    else:
        markdown = MarkdownRenderer.render(report)
        Path(args.out).write_text(markdown, encoding="utf-8")
    return 0


def _build_judgments_by_item_id(
    judgments_data: List[Dict[str, Any]],
    candidate_item_ids: List[str],
) -> Dict[str, ReasoningResult]:
    candidate_item_id_set = set(candidate_item_ids)
    judgments_by_item_id = {}

    for judgment_data in judgments_data:
        item_id = judgment_data["itemId"]
        if item_id in judgments_by_item_id:
            raise ValueError(f"Duplicate judgment itemId: {item_id}")
        if item_id not in candidate_item_id_set:
            raise ValueError(f"Unexpected judgment itemId: {item_id}")
        judgments_by_item_id[item_id] = _deserialize_reasoning_result(judgment_data)

    for item_id in candidate_item_ids:
        if item_id not in judgments_by_item_id:
            raise ValueError(f"Missing judgment for itemId: {item_id}")

    return judgments_by_item_id


def _serialize_evidence_package(package: EvidencePackage) -> Dict[str, Any]:
    return {
        "item": asdict(package.item),
        "candidates": [
            _serialize_candidate(candidate) for candidate in package.candidates
        ],
    }


def _serialize_candidate(candidate: CandidateEvidence) -> Dict[str, Any]:
    return {
        "blockIndex": candidate.blockIndex,
        "userLocator": asdict(candidate.userLocator),
        "matchedKeywords": candidate.matchedKeywords,
        "exactText": candidate.exactText,
        "preContext": candidate.preContext,
        "postContext": candidate.postContext,
        "nearbyImages": [asdict(image) for image in candidate.nearbyImages],
        "rowIndex": candidate.rowIndex,
    }


def _deserialize_evidence_package(data: Dict[str, Any]) -> EvidencePackage:
    item_data = _require_dict(data, "item")
    candidates_data = _require_list(data, "candidates")
    return EvidencePackage(
        item=ChecklistItem(
            itemId=item_data["itemId"],
            name=item_data["name"],
            requirement=item_data["requirement"],
            note=item_data["note"],
        ),
        candidates=[
            _deserialize_candidate(candidate_data)
            for candidate_data in candidates_data
        ],
    )


def _deserialize_candidate(data: Dict[str, Any]) -> CandidateEvidence:
    locator_data = _require_dict(data, "userLocator")
    images_data = _require_list(data, "nearbyImages")
    return CandidateEvidence(
        blockIndex=data["blockIndex"],
        userLocator=UserFacingLocator(
            sourceDocName=locator_data["sourceDocName"],
            headingPath=locator_data["headingPath"],
            nearestHeading=locator_data["nearestHeading"],
            nearbyText=locator_data["nearbyText"],
            locatorHint=locator_data["locatorHint"],
            evidenceType=locator_data["evidenceType"],
        ),
        matchedKeywords=data["matchedKeywords"],
        exactText=data["exactText"],
        preContext=data["preContext"],
        postContext=data["postContext"],
        nearbyImages=[
            ImageObject(
                imageId=image_data["imageId"],
                anchorBlockIndex=image_data["anchorBlockIndex"],
                anchorParagraphIndex=image_data["anchorParagraphIndex"],
                nearbyText=image_data["nearbyText"],
                relationshipId=image_data["relationshipId"],
                contentRecognized=image_data["contentRecognized"],
                reason=image_data["reason"],
            )
            for image_data in images_data
        ],
        rowIndex=data["rowIndex"],
    )


def _deserialize_reasoning_result(data: Dict[str, Any]) -> ReasoningResult:
    return ReasoningResult(
        status=EvidenceStatus(data["status"]),
        reason=data["reason"],
        judgmentBasis=data["judgmentBasis"],
        manualCheckPrompt=data["manualCheckPrompt"],
    )


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _write_json(path: str, data: Dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _require_schema_version(
    payload: Dict[str, Any],
    expected_version: str,
    label: str,
) -> None:
    actual_version = payload.get("schemaVersion")
    if actual_version != expected_version:
        raise ValueError(
            f"Invalid {label} schemaVersion: expected "
            f"{expected_version}, got {actual_version}"
        )


def _require_dict(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data[key]
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object.")
    return value


def _require_list(data: Dict[str, Any], key: str) -> List[Any]:
    value = data[key]
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array.")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
