# proposal-point-checker

Use this skill when you need to help a human reviewer check a DOCX proposal against a manually prepared CSV checklist, locate candidate evidence, and produce Markdown or CSV review reports for human verification.

This skill is an evidence-location and review-assistance workflow. It is not a legal or compliance adjudication system.

## What This Skill Can Do

The current v0.1 pipeline supports:

- Parsing a CSV checklist with the columns `序号`, `审核点名称`, `审核要求`, and `审核说明`.
- Parsing a single DOCX proposal in physical document order.
- Extracting paragraph text, table rows, heading context, and lightweight image anchors.
- Retrieving candidate evidence from parsed text, table rows, and nearby image-anchor text.
- Passing retrieved evidence packages into a caller-provided reasoning adapter.
- Aggregating judged evidence packages.
- Rendering a deterministic Markdown report for human review.
- Rendering a deterministic CSV report for Excel / WPS manual review.

The supported end-to-end shape is:

```text
CSV checklist
-> DOCX parsing
-> candidate evidence retrieval
-> caller-provided evidence reasoning
-> report aggregation
-> Markdown or CSV rendering
```

## Hard Limits

The v0.1 package does not include a real LLM provider.

Agents must not claim this skill can independently perform semantic reasoning unless they have explicitly supplied an `LLMProviderAdapter` implementation or an equivalent external judgment step.

Unsupported in v0.1:

- PDF input.
- OCR.
- Image content recognition.
- DOCX rendered page number mapping.
- Multi-file proposal packages.
- Electronic bidding system field checks.
- Seal authenticity judgment.
- Certificate authenticity judgment.
- Final bid rejection, compliance, pass/fail, or risk-level decisions.

Detected images are only image anchors. The system records where an image appears and nearby text; it does not read image content.

## Evidence Status Contract

Reasoning output must use exactly one of these six evidence statuses:

- `CLEAR_EVIDENCE`
- `SUSPECTED_EVIDENCE`
- `CONFLICTING_EVIDENCE`
- `NOT_FOUND`
- `INSUFFICIENT_EVIDENCE`
- `UNABLE_TO_JUDGE`

Do not convert these statuses into pass/fail, compliant/non-compliant, risk level, or bid rejection conclusions. The report is for human review.

## Execution Modes

### Mode A: Python SDK Injection

Use this when the Agent or host application can write Python glue code.

The caller imports the biddeer_checker modules, implements `LLMProviderAdapter`, and injects it into `ReasoningEngine`.

Minimal shape:

```python
from biddeer_checker.checklist_model.parser import CSVChecklistParser
from biddeer_checker.document_parser.parser import DocxDocumentParser
from biddeer_checker.evidence_retrieval.engine import retrieve_evidence
from biddeer_checker.evidence_reasoning.engine import ReasoningEngine
from biddeer_checker.report_renderer.aggregator import ReportAggregator
from biddeer_checker.report_renderer.csv_renderer import CSVRenderer
from biddeer_checker.report_renderer.markdown_renderer import MarkdownRenderer

items, errors = CSVChecklistParser().parse("checklist.csv")
if errors:
    raise ValueError(errors)

document = DocxDocumentParser().parse("proposal.docx")
packages = retrieve_evidence(items, document)

engine = ReasoningEngine(adapter=YourLLMProviderAdapter())
judged = [engine.judge(package) for package in packages]

report = ReportAggregator.aggregate(judged)
markdown = MarkdownRenderer.render(report)
csv_report = CSVRenderer.render(report)
```

`YourLLMProviderAdapter` is supplied by the caller. The package does not provide an OpenAI, Gemini, Claude, or private gateway implementation.

See `examples/bridge_adapter_template.py` for the expected adapter shape.

### Mode B: Split-Step CLI Workflow

Use this when the Agent runtime can run shell commands and can prepare external judgments between deterministic retrieval and deterministic report rendering.

The currently supported module entrypoints are:

```bash
python -m biddeer_checker.cli retrieve --csv checklist.csv --docx proposal.docx --out candidates.json
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.md
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.csv --format csv
```

Do not assume a console script such as `biddeer_checker` is installed unless a future packaging stage explicitly adds and validates that entrypoint.

For lightweight Agent runtimes, the supported workflow is:

1. Run `python -m biddeer_checker.cli retrieve` with a CSV checklist and DOCX proposal to write `candidates.json`.
2. Judge each candidate package externally through the Agent runtime, a human process, or a mock workflow.
3. Write `judgments.json` using the current judgments schema and exactly one of the six `EvidenceStatus` values for each checklist item.
4. Run `python -m biddeer_checker.cli report` with `candidates.json` and `judgments.json` to write the Markdown report.
5. Add `--format csv` when the reviewer needs a CSV report for Excel / WPS manual review.

The `retrieve` command does not call a real LLM and does not support PDF, OCR, image content recognition, or rendered page mapping.

The `report` command does not include a real LLM Provider. It consumes externally prepared judgments and renders human-review Markdown or CSV reports. CSV is a review-assist format for filtering and checking evidence in Excel / WPS. It must not be used to output final bid rejection, pass/fail, compliance adjudication, or risk-level decisions.

## Mock And Demo Boundary

Mock providers used by tests are acceptance-test fixtures only. They prove the pipeline wiring and six-status report behavior; they are not real LLM reasoning and must not be presented as model capability.

## Input Rules

Checklist CSV:

```csv
序号,审核点名称,审核要求,审核说明
ITEM-001,项目经理配置要求,须配备1名具备相关高级职称的项目经理。,无
```

Proposal document:

- Must be DOCX.
- Must be readable, unencrypted Office Open XML.
- Should contain extractable text for reliable retrieval.
- WPS documents should be saved as standard `.docx` first.

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
- Present the six evidence statuses as Chinese evidence-location states.
- Avoid pass/fail, bid rejection, and risk-level wording.

## When To Stop

Stop and ask for human direction if:

- You need a real LLM provider but none has been supplied.
- The user asks for PDF, OCR, image content recognition, or page mapping.
- The task requires judging certificate authenticity, seal authenticity, or final bid compliance.
- The available evidence is only inside images.
- You would need to add dependencies, add console script entrypoints, or expand CLI/runtime behavior beyond Markdown/CSV report rendering.
