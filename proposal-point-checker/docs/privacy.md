# Privacy

## Local Processing

BidDeer Proposal Point Checker is designed for local, evidence-based review.

- All document processing and evidence retrieval is performed locally on your machine.
- No proposal content, checklist data, or extracted evidence is uploaded to external servers.
- Optional local OCR (PaddleOCR) runs entirely on your machine and does not upload images or documents.

## Public Examples

- Public examples in this repository use synthetic content only.
- Examples do not contain real tender documents, customer names, or company data.
- Do not submit real bid documents, customer information, or sensitive content as public examples, issues, or pull requests.

## Recommendations for Real Use

- For real bid documents, use a local or private deployment.
- Keep customer files and generated artifacts in a per-task workspace outside the Skill directory.
- Do not upload sensitive project files to public platforms.
- All high-risk review results should be verified by qualified personnel.

## Data Boundaries

- The Skill reads only the documents you explicitly provide as input.
- The Skill writes outputs only to the paths you explicitly specify.
- No telemetry, usage data, or analytics are collected.
