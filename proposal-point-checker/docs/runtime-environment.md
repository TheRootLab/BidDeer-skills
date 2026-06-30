# proposal-point-checker Runtime Environment

This document defines the v0.1 runtime environment and customer deployment compatibility contract for `proposal-point-checker`. It documents execution assumptions only; it does not add packaging behavior, dependencies, or runtime features.

## Supported Execution Mode

v0.1 officially supports source-checkout execution mode.

The Skill is run from a checked-out copy of the public repository, not from a globally installed console script. The standard invocation is:

```bash
cd "<skill_root>"
python -m biddeer_checker.cli ...
```

Running `python -m biddeer_checker.cli` from an arbitrary directory may fail unless the package has been installed into that Python environment or the process is already running from the Skill root.

## Canonical Skill Root

The canonical public Skill root is:

```text
skill_root = proposal-point-checker/
```

Do not use or recreate the obsolete path:

```text
skills/proposal-point-checker/
```

Deployment scripts, Agent configuration, and documentation should resolve the checked-out `proposal-point-checker/` directory as the Skill root.

## Command Working Directory

Agent runtimes should use the Skill root as the command working directory.

```bash
cd "<skill_root>"
```

All documented CLI examples assume they are run from `<skill_root>` unless explicitly stated otherwise.

## Skill Root vs Task Workspace

Keep runtime code and per-task data in separate directories:

```text
skill_root = installed Skill directory
task_workspace = per-task directory for uploaded checklist, proposal, candidates, judgments, reports, and logs
```

The Skill directory should not be used as the user data directory. Customer files and generated artifacts should live in the task workspace.

A typical Agent invocation uses the Skill root as `cwd` and absolute task-workspace paths for data:

```bash
cd "<skill_root>"

python -m biddeer_checker.cli retrieve \
  --csv "<absolute_task_workspace>/checklist.csv" \
  --proposal "<absolute_task_workspace>/proposal.pdf" \
  --out "<absolute_task_workspace>/candidates.json"

python -m biddeer_checker.cli report \
  --candidates "<absolute_task_workspace>/candidates.json" \
  --judgments "<absolute_task_workspace>/judgments.json" \
  --out "<absolute_task_workspace>/report.md"

python -m biddeer_checker.cli report \
  --candidates "<absolute_task_workspace>/candidates.json" \
  --judgments "<absolute_task_workspace>/judgments.json" \
  --out "<absolute_task_workspace>/report.csv" \
  --format csv
```

## Read-Mostly Installation Directory

After installation, the Skill directory should be treated as read-mostly. All runtime artifacts should be written to the external task workspace via explicit `--out` paths.

Customer environments may install the Skill under permission-restricted locations such as:

```text
C:\Program Files\...
/opt/...
enterprise-managed software directories
read-only or permission-restricted paths
```

Do not write customer uploads, candidates, judgments, reports, or logs into the Skill installation directory.

## Python Version and Interpreter

Python 3.10+ is recommended. Python 3.11 or 3.12 are preferred validation environments.

In commands, `python` means the Python executable from the active virtual environment, not necessarily the system Python. Check the interpreter before processing customer files:

```bash
python -c "import sys; print(sys.executable); print(sys.version)"
```

If the command reports a different interpreter from the intended virtual environment, fix the environment before continuing.

## Virtual Environment

A virtual environment is recommended, but the venv directory name is not a runtime contract.

For example, either of these macOS/Linux layouts is acceptable:

```bash
python -m venv venv
source venv/bin/activate
```

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell example:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Do not hardcode one venv directory name in Agent runtime logic.

## Dependencies

Install runtime dependencies from the Skill root:

```bash
python -m pip install -r requirements.txt
```

Install development and smoke-test dependencies when tests are required:

```bash
python -m pip install -r requirements-dev.txt
```

The runtime contract does not add any dependency.

## CLI Entrypoint

The supported CLI entrypoint is the Python module:

```bash
python -m biddeer_checker.cli retrieve ...
python -m biddeer_checker.cli report ...
```

Do not assume a console script such as `biddeer_checker` exists unless a future packaging PR explicitly adds and validates it.

## Path Handling Rules

Human demo commands may use relative paths. Agent runtime integration should use absolute paths for all user inputs and outputs, including:

```text
--csv
--proposal
--candidates
--judgments
--out
```

All documented customer or Agent examples should quote file paths. Quoting avoids failures when paths contain spaces, non-ASCII characters, or shell-significant characters. Output paths are selected by `--out`; production integrations must not hardcode `/tmp` as the only output location.

## Windows PowerShell Example

Windows paths may contain Chinese characters, spaces, or parentheses, so quote every customer and task-workspace path:

```powershell
cd "D:\BidDeer\skills\proposal-point-checker"

python -m biddeer_checker.cli retrieve `
  --csv "D:\BidDeer Tasks\项目A\检查清单.csv" `
  --proposal "D:\BidDeer Tasks\项目A\投标文件.pdf" `
  --out "D:\BidDeer Tasks\项目A\candidates.json"

python -m biddeer_checker.cli report `
  --candidates "D:\BidDeer Tasks\项目A\candidates.json" `
  --judgments "D:\BidDeer Tasks\项目A\judgments.json" `
  --out "D:\BidDeer Tasks\项目A\report.csv" `
  --format csv
```

## Post-Install Preflight

Run this minimum check from the installed Skill root:

```bash
cd "<skill_root>"

python --version
python -c "import sys; print(sys.executable)"
python -c "import biddeer_checker; print('biddeer_checker import ok')"
python -c "import pypdf; print('pypdf', pypdf.__version__)"
python -m biddeer_checker.cli --help
```

If any preflight command fails, the installation is not ready for customer files.

## Post-Install Demo Smoke Validation

Use the fully synthetic basic PDF demo to validate an installation without customer data:

```bash
cd "<skill_root>"

python -m biddeer_checker.cli retrieve \
  --csv "examples/demo_pdf/synthetic_checklist.csv" \
  --proposal "examples/demo_pdf/synthetic_proposal_text_layer.pdf" \
  --out "<absolute_task_workspace>/demo_candidates.json"

python -m biddeer_checker.cli report \
  --candidates "<absolute_task_workspace>/demo_candidates.json" \
  --judgments "examples/demo_pdf/sample_judgments.json" \
  --out "<absolute_task_workspace>/demo_report.md"

python -m biddeer_checker.cli report \
  --candidates "<absolute_task_workspace>/demo_candidates.json" \
  --judgments "examples/demo_pdf/sample_judgments.json" \
  --out "<absolute_task_workspace>/demo_report.csv" \
  --format csv
```

The installation smoke validation succeeds when:

1. `demo_candidates.json` is generated.
2. The Markdown report is generated.
3. The CSV report is generated.
4. PDF evidence locations include the filename and physical page number.
5. All output files are written outside the Skill directory.

Use `examples/demo_reasoning/` when separately validating six-status report behavior.

## LLM Provider Boundary

v0.1 does not include a real LLM provider.

The deterministic pipeline is:

```text
CSV checklist -> proposal parsing -> candidate evidence retrieval -> report rendering
```

The reasoning step must be supplied externally by one of:

```text
caller-provided LLMProviderAdapter
Agent runtime judgment step
human-prepared judgments
mock judgments for demos/tests
```

The Skill must not claim independent semantic reasoning unless an external adapter or judgment step is explicitly supplied.

## External Tools Boundary

Normal runtime use does not require:

```text
LibreOffice
WPS
Word
OCR tools
PyMuPDF
pdfplumber
PaddleOCR
RapidOCR
Tesseract
OpenCV
real LLM SDKs
```

LibreOffice, WPS, or Word may be used only to regenerate demo PDFs from DOCX sources. They are optional demo-generation tools, not runtime dependencies.

## Offline and Intranet Deployment

Online pip install is the default development path. Customer or intranet deployments may require a wheelhouse, offline package bundle, or internal PyPI mirror.

This document does not implement offline packaging. It records the deployment consideration so deployment owners can prepare approved dependency artifacts before installation.

## PDF and DOCX Boundaries

PDF input support is limited to text-layer PDFs parsed locally with `pypdf==6.14.2`.

The following remain unsupported:

```text
scanned PDF
image-only PDF
OCR
PDF image extraction
coordinate highlighting
seal/signature authenticity judgment
certificate authenticity judgment
```

DOCX page numbers must not be fabricated. Only PDF evidence locations may use physical PDF page numbers such as:

```text
<filename> > 第 N 页
```

## Key Deployment Rule

```text
Use Skill root as cwd.
Use absolute task-workspace paths for all user inputs and outputs.
Treat the Skill directory as read-mostly after installation.
```
