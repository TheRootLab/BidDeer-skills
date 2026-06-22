# proposal-point-checker

`proposal-point-checker` is the first BidDeer Agent Skill package. It helps reviewers compare a manually prepared CSV checklist against a DOCX proposal, locate candidate evidence, and render a Markdown review report.

The package is designed as a human-review assistant. It does not produce final bid rejection, compliance, pass/fail, or risk-level decisions.

## Current v0.1 Scope

Supported:

- CSV checklist parsing and validation.
- Single DOCX proposal parsing.
- Paragraph, heading, and table-row extraction.
- Lightweight image-anchor detection.
- Deterministic candidate evidence retrieval from text, tables, and nearby image-anchor text.
- Six-status evidence reasoning through a caller-provided adapter.
- Markdown report aggregation and rendering.

Deferred:

- PDF input.
- OCR.
- Image content recognition.
- Rendered page number mapping.
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

## Quick Start

The repository includes a fully synthetic proposal, checklist, and mock judgments, so the retrieve/report demo can run immediately after installation. None of these files contain real customers, projects, companies, certificates, or bidding materials.

1. Run the `retrieve` stage with the included synthetic proposal:
   ```bash
   python -m biddeer_checker.cli retrieve \
     --csv examples/sample_checklist.csv \
     --docx examples/sample_proposal.docx \
     --out candidates.json
   ```

2. Use `examples/sample_judgments.json` for the demo. It contains hand-authored mock evidence judgments for the synthetic inputs; it does not come from a real LLM and does not express a final bid rejection, pass/fail result, or risk level.

3. Run the `report` stage to generate the Markdown report:
   ```bash
   python -m biddeer_checker.cli report \
     --candidates candidates.json \
     --judgments examples/sample_judgments.json \
     --out report.md
   ```

To regenerate the synthetic DOCX optionally, run:

```bash
python examples/generate_sample_docx.py examples/sample_proposal.docx
```

The committed DOCX is ready to use; regeneration is not required for the demo.

## Pipeline

```text
CSV checklist
-> DOCX document parsing
-> candidate evidence retrieval
-> evidence reasoning through injected adapter
-> report aggregation
-> Markdown rendering
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

### Proposal DOCX

The proposal file must be a readable `.docx` file. WPS documents should be saved as standard Office Open XML `.docx` before processing.

The parser extracts text, tables, heading context, and image anchors. It does not read image content.

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
from biddeer_checker.document_parser.parser import DocxDocumentParser
from biddeer_checker.evidence_retrieval.engine import retrieve_evidence
from biddeer_checker.evidence_reasoning.engine import ReasoningEngine
from biddeer_checker.report_renderer.aggregator import ReportAggregator
from biddeer_checker.report_renderer.markdown_renderer import MarkdownRenderer

from your_project.adapters import YourLLMProviderAdapter

items, errors = CSVChecklistParser().parse("examples/sample_checklist.csv")
if errors:
    raise ValueError(errors)

document = DocxDocumentParser().parse("proposal.docx")
packages = retrieve_evidence(items, document)

engine = ReasoningEngine(adapter=YourLLMProviderAdapter())
judged_packages = [engine.judge(package) for package in packages]

report = ReportAggregator.aggregate(judged_packages)
markdown = MarkdownRenderer.render(report)
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
python -m biddeer_checker.cli retrieve --csv examples/sample_checklist.csv --docx proposal.docx --out candidates.json
python -m biddeer_checker.cli report --candidates candidates.json --judgments judgments.json --out report.md
```

No console script entrypoint is currently documented for this package. Use the module form above unless a future packaging stage adds and validates a separate entrypoint.

### `retrieve`

`retrieve` reads a CSV checklist and a DOCX proposal, then writes `candidates.json`.

It performs deterministic parsing and candidate evidence retrieval only. It does not call a real LLM, does not perform evidence reasoning, and does not add support for PDF, OCR, image content recognition, or rendered page mapping.

### `report`

`report` reads `candidates.json` and `judgments.json`, then writes a Markdown report.

`judgments.json` must be prepared externally by an Agent runtime, a human review process, or a mock workflow. The package does not include a built-in real LLM provider and does not manage provider credentials.

The generated report uses the six evidence statuses listed above. It must not be treated as a final bid rejection, pass/fail, compliance adjudication, or risk-level verdict.

## Examples

This package includes:

- `examples/sample_checklist.csv`: a small synthetic checklist.
- `examples/sample_proposal.docx`: a ready-to-use, fully synthetic proposal covering the sample checklist scenarios.
- `examples/sample_judgments.json`: hand-authored mock evidence judgments for the synthetic inputs; they do not come from a real LLM or provide final business decisions.
- `examples/bridge_adapter_template.py`: a template for implementing an external reasoning adapter.
- `examples/generate_sample_docx.py`: an optional helper that can regenerate the synthetic DOCX when `python-docx` is available.

The examples are synthetic and do not use real bidding documents.

## Development Boundary For This Package Stage

Release package documentation updates must not:

- Modify `biddeer_checker/**`.
- Modify `tests/**`.
- Add a real LLM provider.
- Modify CLI implementation or add console script entrypoints.
- Add PDF/OCR/image recognition/page mapping.
- Change fixture semantics or validation assertions.
