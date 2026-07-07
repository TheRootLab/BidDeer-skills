# Known Limitations

## Scope Limitations

- This Skill does not guarantee bid success.
- This Skill does not guarantee non-rejection.
- This Skill does not make final compliance decisions.
- This Skill does not replace legal, commercial, or tender expert review.

## Authenticity Limitations

- This Skill does not verify certificate authenticity.
- This Skill does not verify seal authenticity.
- This Skill does not verify signature authenticity.
- The Skill may locate references to certificates, seals, or signatures but cannot confirm their validity.

## Technical Limitations

- OCR quality depends on document quality, image resolution, and the local OCR runtime.
- Scanned or image-only PDFs are not supported for text retrieval.
- Text extraction is limited to text-layer PDFs and DOCX files.
- Embedded image text is not automatically integrated into evidence retrieval results.
- DOCX rendered page numbers are not available.

## Evidence Limitations

- Ambiguous or missing evidence must be reviewed by humans.
- The Skill returns evidence excerpts based on text matching; it does not independently verify the truth or accuracy of statements in the proposal.
- Evidence statuses are review-assistance labels, not final business judgments.
- The Skill does not assess risk levels or make risk judgments.

## Deployment Limitations

- The Skill requires a Python 3.10+ runtime environment.
- A virtual environment is recommended for dependency isolation.
- Optional OCR features require additional dependencies and local model files.
- GPU acceleration for OCR is experimental and requires explicit configuration.
