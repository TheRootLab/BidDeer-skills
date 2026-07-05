# proposal-point-checker

Use this skill when you need to help a human reviewer check a DOCX or text-layer PDF proposal against a manually prepared CSV checklist, locate candidate evidence, and produce Markdown or CSV review reports for human verification.

This skill is an evidence-location and review-assistance workflow. It is not a legal or compliance adjudication system.

## What This Skill Can Do

The current v0.1 pipeline supports:

- Parsing a CSV checklist with the columns `序号`, `审核点名称`, `审核要求`, and `审核说明`.
- Parsing a single DOCX proposal or text-layer PDF proposal in physical document order.
- Recommending unified CLI input using `--proposal` for both DOCX and text-layer PDF.
- Local PDF text extraction using `pypdf==6.14.2`.
- Explicit local export of extractable embedded PDF raster images.
- Targeted embedded-image extraction from pages selected by existing retrieval,
  with checklist IDs and retrieval-context text in an
  `image-evidence-v0.1` manifest.
- Optional local PaddleOCR review of already-extracted embedded-image
  artifacts through the separate `image-ocr-review` command.
- `paddleocr-result-v0.1` artifacts and a supplemental manual-review report
  that remain separate from candidate retrieval and final bidder reports.
- Extracting paragraph text, table rows, heading context, and lightweight image anchors.
- Retrieving candidate evidence from parsed text, table rows, and nearby image-anchor text.
- Passing retrieved evidence packages into a caller-provided reasoning adapter.
- Aggregating judged evidence packages.
- Rendering a deterministic Markdown report for human review.
- Rendering a deterministic CSV report for Excel / WPS manual review, featuring PDF page-level provenance (e.g. `text_layer_chinese.pdf > 第 1 页`).

The supported end-to-end shape is:

```text
CSV checklist
-> DOCX or PDF parsing
-> candidate evidence retrieval
-> caller-provided evidence reasoning
-> report aggregation
-> Markdown or CSV rendering
```

An optional, separate review branch is:

```text
extracted embedded PDF images
-> local image-ocr-review
-> supplemental OCR artifacts and manual-review report
```

## Hard Limits

The v0.1 package does not include a real LLM provider.

Agents must not claim this skill can independently perform semantic reasoning unless they have explicitly supplied an `LLMProviderAdapter` implementation or an equivalent external judgment step.

Unsupported in v0.1:

- Candidate retrieval from scanned or image-only PDFs.
- Page rendering or OCR fallback for scanned pages.
- OCR integration into candidate evidence retrieval or final bidder reports.
- Image recognition beyond optional local text extraction from already-extracted
  embedded-image artifacts.
- Online recognition-provider calls.
- Online upload of PDFs or extracted images.
- DOCX rendered page number mapping (no fabrication of page numbers for DOCX).
- Multi-file proposal packages.
- Electronic bidding system field checks.
- Seal authenticity judgment.
- Certificate authenticity judgment.
- Final bid rejection, compliance, pass/fail, or risk-level decisions.

Image extraction and OCR are explicit, opt-in steps. The default installation
does not include PaddleOCR, PaddlePaddle, or PaddleX. Optional OCR runs locally
over previously extracted embedded-image artifacts, does not upload content,
and produces supplemental review material only. It does not change retrieval,
judgments, or final reports.

## Evidence Status Contract

Reasoning output must use exactly one of these six evidence statuses:

- `CLEAR_EVIDENCE`
- `SUSPECTED_EVIDENCE`
- `CONFLICTING_EVIDENCE`
- `NOT_FOUND`
- `INSUFFICIENT_EVIDENCE`
- `UNABLE_TO_JUDGE`

Do not convert these statuses into pass/fail, compliant/non-compliant, risk level, or bid rejection conclusions. The report is for human review.

## Runtime Environment Contract

Before executing this skill in an Agent runtime or customer deployment, follow [`docs/runtime-environment.md`](docs/runtime-environment.md).

Key rule:

```text
Use Skill root as cwd. Use absolute task-workspace paths for all user inputs and outputs. Treat the Skill directory as read-mostly after installation.
```

## Execution Modes

### Mode A: Python SDK Injection

Use this when the Agent or host application can write Python glue code.

The caller imports the biddeer_checker modules, implements `LLMProviderAdapter`, and injects it into `ReasoningEngine`.

Minimal shape:

```python
from biddeer_checker.checklist_model.parser import CSVChecklistParser
from biddeer_checker.document_parser.proposal_parser_dispatcher import ProposalParserDispatcher
from biddeer_checker.evidence_retrieval.engine import retrieve_evidence
from biddeer_checker.evidence_reasoning.engine import ReasoningEngine
from biddeer_checker.report_renderer.aggregator import ReportAggregator
from biddeer_checker.report_renderer.csv_renderer import CSVRenderer
from biddeer_checker.report_renderer.markdown_renderer import MarkdownRenderer

items, errors = CSVChecklistParser().parse("checklist.csv")
if errors:
    raise ValueError(errors)

document = ProposalParserDispatcher().parse("proposal.docx")  # or "proposal.pdf"
packages = retrieve_evidence(items, document)

engine = ReasoningEngine(adapter=YourLLMProviderAdapter())
judged = [engine.judge(package) for package in packages]

report = ReportAggregator.aggregate(judged)
markdown = MarkdownRenderer.render(report)
csv_report = CSVRenderer.render(report)
```

`YourLLMProviderAdapter` is supplied by the caller. The package does not provide an OpenAI, Gemini, Claude, or private gateway implementation.

See `examples/tools/bridge_adapter_template.py` for the expected adapter shape.

### Mode B: Split-Step CLI Workflow

Use this when the Agent runtime can run shell commands and can prepare external judgments between deterministic retrieval and deterministic report rendering.

The currently supported module entrypoints are:

```bash
# Recommended unified proposal input:
python -m biddeer_checker.cli retrieve --csv checklist.csv --proposal proposal.docx --out candidates.json
python -m biddeer_checker.cli retrieve --csv checklist.csv --proposal proposal.pdf --out candidates.json
python -m biddeer_checker.cli retrieve --csv checklist.csv --proposal proposal.pdf --out candidates.json --image-mode targeted
python -m biddeer_checker.cli image-ocr-review --workspace "<absolute_task_workspace>" --manifest "<absolute_task_workspace>/image_evidence_manifest.json" --out "<absolute_task_workspace>/image_ocr_review_report.md" --device cpu

# Legacy compatibility (docx only):
python -m biddeer_checker.cli retrieve --csv checklist.csv --docx proposal.docx --out candidates.json

# Generating reports:
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.md
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.csv --format csv
```

Do not assume a console script such as `biddeer_checker` is installed unless a future packaging stage explicitly adds and validates that entrypoint.

For lightweight Agent runtimes, the supported workflow is:

1. Run `python -m biddeer_checker.cli retrieve` with a CSV checklist and a proposal (via `--proposal`) to write `candidates.json`. For a text-layer PDF, add `--image-mode targeted` only when local extraction of embedded raster images from retrieval candidate pages is required.
2. Optionally run local `image-ocr-review` over the extracted-image manifest.
   Keep its artifacts as supplemental manual-review material; do not merge OCR
   text into `candidates.json` or final bidder reports.
3. Judge each candidate package externally through the Agent runtime, a human process, or a mock workflow.
4. Write `judgments.json` using the current judgments schema and exactly one of the six `EvidenceStatus` values for each checklist item.
5. Run `python -m biddeer_checker.cli report` with `candidates.json` and `judgments.json` to write the Markdown report.
6. Add `--format csv` when the reviewer needs a CSV report for Excel / WPS manual review.

The `retrieve` command does not call a real LLM. For DOCX, it parses headings,
paragraph text, tables, and image anchors. For PDF, it parses text-layer content
locally using `pypdf==6.14.2` and retains page numbers; scanned, encrypted, or
invalid PDFs are rejected with clear errors.

`--image-mode disabled` is the default and writes no image manifest.
`--image-mode exhaustive-export` exports all extractable embedded PDF raster
images. `--image-mode targeted` runs after retrieval and exports embedded raster
images only from candidate pages, recording `relatedCheckItemId` and bounded
retrieval-context `nearbyText`. These modes do not perform OCR, image
recognition, provider calls, online upload, page rendering, or authenticity and
business judgments. DOCX image extraction is unsupported and is skipped without
preventing normal text retrieval.

The separate `image-ocr-review` command reads an existing
`image_evidence_manifest.json`, writes one local
`paddleocr-result-v0.1` artifact per selected image, and generates
`image_ocr_review_report.md`. It is optional, requires the separately installed
`requirements-ocr.txt`, and keeps PDF and image content on the local machine.
It does not make validity, authenticity, compliance, pass/fail, bid-rejection,
or risk-level decisions. See [`docs/ocr-setup.md`](docs/ocr-setup.md).

The `report` command does not include a real LLM Provider. It consumes externally prepared judgments and renders human-review Markdown or CSV reports. CSV is a review-assist format for filtering and checking evidence in Excel / WPS. It must not be used to output final bid rejection, pass/fail, compliance adjudication, or risk-level decisions.

## Mock And Demo Boundary

Mock providers used by tests are acceptance-test fixtures only. They prove the pipeline wiring and six-status report behavior; they are not real LLM reasoning and must not be presented as model capability.

Public examples are organized under [`examples/README.md`](examples/README.md):

- `quickstart/` for minimal usage.
- `demos/pdf-basic/` for the basic text-layer PDF demo.
- `demos/reasoning-status/` for the six-status reasoning demo.

## Input Rules

Checklist CSV:

```csv
序号,审核点名称,审核要求,审核说明
ITEM-001,项目经理配置要求,须配备1名具备相关高级职称的项目经理。,无
```

Proposal document:

- Must be DOCX or vector/text-layer PDF.
- If DOCX, must be readable, unencrypted Office Open XML. WPS documents should be saved as standard `.docx` first.
- If PDF, must be parsed locally with `pypdf==6.14.2`. Scanned, encrypted, or
  invalid PDFs are rejected with clear errors. Explicit image modes can extract
  embedded raster objects only. Optional local OCR review is a separate command;
  scanned-page rendering, upload, and seal authenticity checks are not supported.
- Should contain extractable text for reliable retrieval.

## Output Rules

The Markdown report must:

- Preserve the original checklist order.
- Include every checklist item.
- Include candidate evidence and human-facing locator details when available.
- Put non-`CLEAR_EVIDENCE` items into manual review.
- Avoid pass/fail and risk-level wording.

The CSV report must:

- Use `python -m biddeer_checker.cli report --format csv`.
- Preserve the original checklist order.
- Include every checklist item.
- Use fixed columns for reviewer-facing fields, not internal IDs.
- Format PDF evidence locations as `<filename> > 第 N 页` using the physical page number.
- Ensure DOCX page numbers are not fabricated.
- Present the six evidence statuses as Chinese evidence-location states.
- Avoid pass/fail, bid rejection, and risk-level wording.

## When To Stop

Stop and ask for human direction if:

- You need a real LLM provider but none has been supplied.
- The user asks for scanned-PDF OCR, page rendering, OCR integration into
  retrieval or final reports, online recognition, or DOCX page mapping.
- The task requires judging certificate authenticity, seal authenticity, or final bid compliance.
- The available evidence is only inside images and the user has not explicitly
  chosen the optional local extracted-image OCR review workflow.
- You would need to add dependencies beyond the documented optional OCR set,
  add console script entrypoints, or expand CLI/runtime behavior.
