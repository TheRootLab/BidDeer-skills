# Local PaddleOCR Image Review Setup

## Purpose

The optional local image OCR review workflow reads extracted embedded-image
artifacts from an existing `image_evidence_manifest.json`, runs PaddleOCR on
the local machine, writes one `paddleocr-result-v0.1` artifact per selected
image, and generates `image_ocr_review_report.md`.

OCR output is supplemental manual-review material. The workflow does not decide
whether a bid, certificate, seal, signature, or document meets any requirement.

## Privacy boundary

- PDF and image content stays on the local machine.
- The workflow has no online OCR provider and no upload code.
- PaddleOCR package and model download is a separate provisioning action.
- After packages and models are provisioned, inference can run locally from the
  PaddleX model cache.
- Normal workflow output does not log recognized text.

## Optional installation

The default Skill requirements do not install PaddleOCR. Create and activate a
virtual environment, install the normal requirements, then install the optional
OCR pins:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-ocr.txt
```

The validated CPU baseline is:

| Component | Version or model |
| --- | --- |
| PaddleOCR | `3.7.0` |
| PaddlePaddle | `3.3.1` |
| PaddleX OCR extras | `3.7.2` with `ocr-core` |
| Detection model | `PP-OCRv6_tiny_det` |
| Recognition model | `PP-OCRv6_tiny_rec` |
| Device | CPU |

Linux environments may also require the system OpenMP runtime, commonly
provided by the `libgomp1` package.

## Model provisioning

The first engine initialization may download official model artifacts. This is
provisioning, not inference upload. To use the model source validated by the
private local harness:

```bash
export PADDLE_PDX_MODEL_SOURCE=BOS
export PADDLE_PDX_CACHE_HOME="$HOME/.cache/biddeer-paddlex"
```

Run the workflow once on synthetic content to provision the two tiny models.
For later offline runs with the populated cache:

```bash
export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
```

If PaddleOCR is not installed, the command does not import or download it. It
writes `unavailable` OCR artifacts, generates manual-review guidance, and exits
with status `2`.

## Usage

First run `retrieve` with `--image-mode targeted` or
`--image-mode exhaustive-export`. The task workspace must then contain:

```text
<task_workspace>/
  image_evidence_manifest.json
  images/
    <imageId>.png
```

Run:

```bash
python -m biddeer_checker.cli image-ocr-review \
  --workspace "<absolute_task_workspace>" \
  --manifest "<absolute_task_workspace>/image_evidence_manifest.json" \
  --out "<absolute_task_workspace>/image_ocr_review_report.md" \
  --device cpu \
  --det-model PP-OCRv6_tiny_det \
  --rec-model PP-OCRv6_tiny_rec
```

Outputs:

```text
<task_workspace>/
  ocr_results/
    <imageId>.paddleocr.json
  image_ocr_review_report.md
```

The source `image_evidence_manifest.json` is read-only and is not changed.
Per-image recognition errors are written as error artifacts; remaining selected
images continue through the workflow.

## Current limits

- Embedded-image artifacts only; there is no scanned-page rendering fallback.
- CPU-first local execution only; no Docker or GPU-specific production path.
- OCR text is not integrated into evidence retrieval or final bidder reports.
- The workflow does not make pass/fail, bid-rejection, risk-level, validity, or
  authenticity conclusions.
