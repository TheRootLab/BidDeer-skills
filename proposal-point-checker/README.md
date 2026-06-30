# proposal-point-checker

`proposal-point-checker` is the first BidDeer Agent Skill package. It helps reviewers compare a manually prepared CSV checklist against a DOCX or text-layer PDF proposal, locate candidate evidence, and render Markdown or CSV review reports.

The package is designed as a human-review assistant. It does not produce final bid rejection, compliance, pass/fail, or risk-level decisions.

## Current v0.1 Scope

Supported:

- CSV checklist parsing and validation.
- Single DOCX or text-layer PDF proposal parsing.
- Recommended unified CLI input using `--proposal` for both DOCX and text-layer PDF.
- Local PDF text extraction using `pypdf==6.14.2`.
- Paragraph, heading, and table-row extraction.
- Lightweight image-anchor detection.
- Deterministic candidate evidence retrieval from text, tables, and nearby image-anchor text.
- Six-status evidence reasoning through a caller-provided adapter.
- Markdown report aggregation and rendering.
- CSV report rendering with PDF page-level provenance (e.g. `text_layer_chinese.pdf > 第 1 页`).

Deferred:

- Scanned or image-only PDF.
- OCR.
- Image content recognition.
- Rendered page number mapping for DOCX.
- Real LLM provider implementation.
- Multi-file proposal package support.
- Seal or certificate authenticity judgment.
- Electronic bidding system field checks.
- Final compliance, bid rejection, pass/fail, or risk-level output.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/TheRootLab/BidDeer-skills.git
   ```

2. Navigate to the package directory:
   ```bash
   cd BidDeer-skills/proposal-point-checker
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment:
   - For macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - For Windows PowerShell:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

5. Install the required dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

6. Install development dependencies for smoke tests:
   ```bash
   python -m pip install -r requirements-dev.txt
   ```

7. Verify the package import:
   ```bash
   python -c "import biddeer_checker; print('biddeer_checker imported successfully')"
   ```

8. Verify the CLI help:
   ```bash
   python -m biddeer_checker.cli --help
   ```

9. Run the smoke tests:
   ```bash
   python -m pytest smoke_tests/test_cli_smoke.py -v
   ```

## Runtime Environment

For customer deployment, Agent integration, working-directory rules, virtualenv expectations, path handling, and post-install validation, see [`docs/runtime-environment.md`](docs/runtime-environment.md).

Key rule:

```text
Use Skill root as cwd. Use absolute task-workspace paths for user inputs and outputs. Treat the Skill directory as read-mostly after installation.
```

## Quick Start

1. Generate a synthetic DOCX file for testing:
   ```bash
   python examples/generate_sample_docx.py sample_proposal.docx
   ```

2. Run the `retrieve` stage to extract candidate evidence (recommended using `--proposal`):
   ```bash
   python -m biddeer_checker.cli retrieve \
     --csv examples/sample_checklist.csv \
     --proposal sample_proposal.docx \
     --out candidates.json
   ```

   Or run using a text-layer PDF:
   ```bash
   python -m biddeer_checker.cli retrieve \
     --csv examples/sample_checklist.csv \
     --proposal tests/fixtures/pdf/text_layer_chinese.pdf \
     --out candidates.json
   ```

   *Note: `--docx` is kept for backward compatibility. New workflows should use `--proposal`.*

3. **External Judgments Required:** `judgments.json` must be prepared externally. This package does not contain a built-in real LLM provider. You must construct or mock `judgments.json` based on the `candidates.json` structure for testing.

4. Run the `report` stage to generate the Markdown report. Markdown remains the default output format:
   ```bash
   python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.md
   ```

5. To generate a CSV report for Excel / WPS manual review, pass `--format csv` explicitly:
   ```bash
   python -m biddeer_checker.cli report \
     --candidates candidates.json \
     --judgments judgments.json \
     --out report.csv \
     --format csv
   ```

The repository may include `examples/sample_judgments.json` on branches or releases that publish ready-to-run demo samples. Treat that file as mock judgment data for report rendering only; it is not produced by a built-in real LLM provider.

## Pipeline

```text
CSV checklist
-> DOCX or PDF document parsing
-> candidate evidence retrieval
-> evidence reasoning through injected adapter
-> report aggregation
-> Markdown or CSV rendering
```

The deterministic stages are implemented in the shared `biddeer_checker/` package in this repository. The reasoning stage requires the caller to provide an adapter implementing the current `LLMProviderAdapter` interface.

## Input Contracts

### Checklist CSV

The CSV checklist must include these columns:

```csv
序号,审核点名称,审核要求,审核说明
```

Example:

```csv
序号,审核点名称,审核要求,审核说明
ITEM-001,项目经理配置要求,须配备1名具备相关高级职称的项目经理。,无
```

### Proposal Input

The proposal input (supplied via `--proposal`) accepts:
- **DOCX**: The proposal file must be a readable `.docx` file. WPS documents should be saved as standard Office Open XML `.docx` before processing. The parser extracts text, tables, heading context, and image anchors. It does not read image content.
- **PDF**: A valid vector/text-layer `.pdf` file. Scanned, encrypted, or image-only PDFs are rejected. It does not support OCR, PDF image extraction, or signature/seal authenticity verification.

When the input is a text-layer PDF, the generated CSV report's `证据位置` (Evidence Location) column will include the PDF filename and the original 1-based page number, formatted as:
`text_layer_chinese.pdf > 第 1 页`
*Note: DOCX inputs do not provide rendered page numbers; page numbers will not be fabricated for DOCX.*

## Evidence Statuses

The reasoning adapter must return one of these exact values:

| Status | Meaning |
| --- | --- |
| `CLEAR_EVIDENCE` | Clear matching evidence was found. |
| `SUSPECTED_EVIDENCE` | Related evidence was found, but manual confirmation is needed. |
| `CONFLICTING_EVIDENCE` | Evidence appears to conflict with the checklist requirement. |
| `NOT_FOUND` | No candidate evidence was found. |
| `INSUFFICIENT_EVIDENCE` | Partial evidence exists, but key information is missing or image-only. |
| `UNABLE_TO_JUDGE` | The available context cannot support a stable judgment. |

These are evidence states, not final business decisions.

## Python Integration

The current repository exposes the runtime through Python modules under `biddeer_checker/`.

```python
from biddeer_checker.checklist_model.parser import CSVChecklistParser
from biddeer_checker.document_parser.proposal_parser_dispatcher import ProposalParserDispatcher
from biddeer_checker.evidence_retrieval.engine import retrieve_evidence
from biddeer_checker.evidence_reasoning.engine import ReasoningEngine
from biddeer_checker.report_renderer.aggregator import ReportAggregator
from biddeer_checker.report_renderer.csv_renderer import CSVRenderer
from biddeer_checker.report_renderer.markdown_renderer import MarkdownRenderer

from your_project.adapters import YourLLMProviderAdapter

items, errors = CSVChecklistParser().parse("examples/sample_checklist.csv")
if errors:
    raise ValueError(errors)

document = ProposalParserDispatcher().parse("proposal.docx")  # or "proposal.pdf"
packages = retrieve_evidence(items, document)

engine = ReasoningEngine(adapter=YourLLMProviderAdapter())
judged_packages = [engine.judge(package) for package in packages]

report = ReportAggregator.aggregate(judged_packages)
markdown = MarkdownRenderer.render(report)
csv_report = CSVRenderer.render(report)
```

The adapter must implement:

```python
invoke_reasoning(item: ChecklistItem, context_text: str) -> ReasoningResult
```

See `examples/bridge_adapter_template.py` for a non-functional template. It intentionally does not call any real provider.

## No Built-In Real LLM Provider

v0.1 does not include an OpenAI, Gemini, Claude, or private gateway adapter.

The host application is responsible for:

- Selecting a provider.
- Managing credentials.
- Sending prompts or context to the provider.
- Parsing provider output.
- Returning a complete `ReasoningResult`.

This keeps the package lightweight and avoids hard-coding model vendors or credentials into the Skill package.

## Split-Step CLI Usage

The implemented split-step CLI is available through the Python module entrypoint:

```bash
# Recommended unified proposal input:
python -m biddeer_checker.cli retrieve --csv examples/sample_checklist.csv --proposal proposal.docx --out candidates.json
python -m biddeer_checker.cli retrieve --csv examples/sample_checklist.csv --proposal proposal.pdf --out candidates.json

# Legacy docx compatibility (kept for backward compatibility):
python -m biddeer_checker.cli retrieve --csv examples/sample_checklist.csv --docx proposal.docx --out candidates.json

# Generating reports:
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.md
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.csv --format csv
```

No console script entrypoint is currently documented for this package. Use the module form above unless a future packaging stage adds and validates a separate entrypoint.

### `retrieve`

`retrieve` reads a CSV checklist and a DOCX or text-layer PDF proposal, then writes `candidates.json`.

It performs deterministic parsing and candidate evidence retrieval only. It does not call a real LLM and does not perform evidence reasoning.

Supported formats:
- **DOCX**: Parses text, tables, headings, and image anchors.
- **PDF**: Parses text-layer PDFs locally using `pypdf==6.14.2` and extracts physical pages. Image-only (scanned), encrypted, or invalid PDFs are rejected with clear errors. OCR and image content extraction are not supported.

### `report`

`report` reads `candidates.json` and `judgments.json`, then writes a Markdown report by default.

`judgments.json` must be prepared externally by an Agent runtime, a human review process, or a mock workflow. The package does not include a built-in real LLM provider and does not manage provider credentials.

Use `--format csv` to write a CSV report with fixed Chinese columns for Excel / WPS manual review. The CLI does not infer the format from the output file suffix; Markdown remains the default unless `--format csv` is provided.

The generated reports use the six evidence statuses listed above. They must not be treated as final bid rejection, pass/fail, compliance adjudication, or risk-level verdicts.

## Examples

This package includes:

- `examples/sample_checklist.csv`: a small synthetic checklist.
- `examples/sample_judgments.json`: mock judgments for demo report rendering when included in the checked-out branch or release.
- `examples/bridge_adapter_template.py`: a template for implementing an external reasoning adapter.
- `examples/generate_sample_docx.py`: a helper that can generate a minimal synthetic DOCX for local experimentation when `python-docx` is available.

The examples are synthetic and do not use real bidding documents.

## Development Boundary For This Package Stage

Release package documentation updates must not:

- Modify `biddeer_checker/**`.
- Modify `tests/**`.
- Add a real LLM provider.
- Modify CLI implementation or add console script entrypoints.
- Add scanned PDF/OCR/image recognition/DOCX page mapping.
- Change fixture semantics or validation assertions.
