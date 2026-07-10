# BidDeer Proposal Point Checker — Skill Behavior

Use this Skill when a user needs to compare a proposal or bid document against a set of user-provided checklist items and produce evidence-based review results for human confirmation.

## Workflow

1. Parse the user-provided checklist items.
2. Inspect the target proposal document (DOCX or text-layer PDF).
3. Match each checklist item against the proposal content.
4. Return a result for each item:
   - Evidence excerpt when matching evidence is found.
   - `not_found` when no matching evidence is found.
   - `partially_found` when only partial evidence is found.
   - `unclear` when the evidence is ambiguous.
   - `not_applicable` when the check item does not apply.
5. Include source location when available.
6. Produce a review report for human confirmation.

## Status Values

Allowed:

- `found`
- `partially_found`
- `not_found`
- `unclear`
- `not_applicable`

Forbidden:

- `pass`
- `fail`
- `rejected`
- `safe`
- `guaranteed`

## Output Fields

| Field | Description |
|---|---|
| `check_id` | Unique identifier for the checklist item |
| `check_item` | Description of the requirement being checked |
| `status` | One of the allowed status values |
| `evidence_excerpt` | Matching text excerpt from the proposal when found |
| `source_location` | Location within the proposal (section, page) when available |
| `notes` | Additional context or instructions for the human reviewer |

## CSV Output Encoding

When producing CSV files that contain Chinese text, the CSV file MUST be written as UTF-8 with BOM.

Reason:

- Chinese Windows Excel/WPS may open CSV files using the local system encoding, such as GBK or GB18030, when no BOM is present.
- UTF-8 without BOM may display Chinese characters as garbled text in Excel/WPS.
- UTF-8 with BOM allows Excel/WPS to correctly detect the file as UTF-8.

Implementation guidance:

- Python: use `encoding="utf-8-sig"` when writing CSV files.
- JavaScript/Node.js: prepend `\ufeff` before writing the CSV string.
- Keep Markdown, JSON, and plain text outputs as normal UTF-8 unless a specific consumer requires otherwise.

For Python CSV generation, use:

```python
import csv

with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "check_id",
            "check_item",
            "status",
            "evidence_excerpt",
            "source_location",
            "notes",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
```

Validation guidance:

```python
from pathlib import Path

data = Path(output_path).read_bytes()
assert data.startswith(b"\xef\xbb\xbf"), "CSV output must include UTF-8 BOM"
```

## Rules

- Never invent evidence.
- Never claim final bid rejection.
- Never claim final compliance.
- Never use pass/fail, rejected, safe, or guaranteed as a status.
- Keep final confirmation with the human reviewer.
- When evidence is ambiguous, return `unclear` and explain why.
- When only partial evidence exists, return `partially_found` and note what is missing.
- When exporting Chinese review results as CSV, use UTF-8 with BOM so the file opens correctly in Windows Excel/WPS.

## Hard Boundaries

- This Skill does not verify certificate, seal, or signature authenticity.
- This Skill does not make risk-level judgments.
- This Skill does not make bid rejection judgments.
- This Skill does not guarantee bid success or non-rejection.
- This Skill does not replace legal, commercial, or tender expert review.

## Public Examples

Use only synthetic examples provided under the `examples/` directory. Do not use real tender documents, customer names, or company data in examples.
