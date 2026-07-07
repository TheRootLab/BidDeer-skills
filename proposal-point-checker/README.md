# BidDeer Proposal Point Checker

A local, checklist-driven proposal review Skill that helps users compare a proposal document against user-provided check items and produce evidence-based review results for human confirmation.

## What It Does

- Accepts a user-provided checklist of inspection points.
- Accepts a proposal or bid document (DOCX or text-layer PDF).
- Checks each checklist item against the proposal content.
- Returns an evidence excerpt when matching content is found.
- Returns a source location when available.
- Assigns a status to each item (found, partially_found, not_found, unclear, not_applicable).
- Produces a review report for human confirmation.

## What It Does Not Do

- Does not guarantee that a bid will not be rejected.
- Does not make automatic bid compliance decisions.
- Does not make automatic legal judgments.
- Does not make final pass/fail decisions.
- Does not verify certificate, seal, or signature authenticity.
- Does not assess risk levels.
- Does not replace human review.

## Inputs

| Input | Format | Required | Description |
|---|---|---|---|
| Checklist | CSV or Markdown | Yes | User-provided inspection points. Each item must include an identifier and requirement description. |
| Proposal | DOCX or text-layer PDF | Yes | The bid or proposal document to be checked against the checklist. |

## Outputs

| Output | Format | Description |
|---|---|---|
| Review report | Markdown or CSV | Item-by-item check results with status, evidence excerpt, source location, and review notes. |

Each checklist item receives one of the following statuses:

| Status | Meaning |
|---|---|
| `found` | Matching evidence was located in the proposal. |
| `partially_found` | Partial or related evidence was found but key details are missing. |
| `not_found` | No matching evidence was located. |
| `unclear` | The available evidence is ambiguous and needs human review. |
| `not_applicable` | The check item does not apply to this proposal. |

## Quick Start

This Skill works with an Agent that reads the user's checklist and proposal, then applies the rules in [`SKILL.md`](SKILL.md).

1. **Prepare a checklist** — create a list of inspection points. See [`examples/checklist.md`](examples/checklist.md) for the format.
2. **Prepare a proposal** — a DOCX or text-layer PDF containing the bid content.
3. **Load the Skill** into your Agent — the Agent reads [`SKILL.md`](SKILL.md) and follows its behavior rules.
4. **The Agent inspects each checklist item** against the proposal and returns:
   - Evidence excerpt when matching content is found
   - `not_found` when no matching content is found
   - `partially_found` when only partial evidence exists
   - `unclear` when evidence is ambiguous
5. **Review the results** — all output must be confirmed by a human reviewer.

See [`examples/`](examples/) for synthetic sample files that demonstrate the workflow.

## Example

- [`examples/checklist.md`](examples/checklist.md) — sample checklist with 6 inspection items.
- [`examples/proposal.md`](examples/proposal.md) — synthetic proposal text for testing.
- [`examples/expected-output.md`](examples/expected-output.md) — expected review output showing all status types.

## Privacy and Local Processing

- All processing is performed locally on your machine.
- No proposal or checklist content is uploaded to external servers.
- Public examples use synthetic content only — no real tender documents, customer names, or company data.
- For real bid documents, use a local or private deployment.
- See [`docs/privacy.md`](docs/privacy.md) for details.

## Human Review Boundary

This Skill is a **review assistant**, not a decision maker.

- Every check result must be reviewed by a qualified human.
- Evidence excerpts are provided for reference, not as final judgment.
- The Skill does not determine whether a bid will be accepted or rejected.
- The Skill does not determine compliance with tender requirements.
- The Skill does not authenticate certificates, seals, or signatures.
- Final confirmation and responsibility remain with the human reviewer.

## Known Limitations

- The Skill does not guarantee bid success or non-rejection.
- OCR quality depends on document quality and the local runtime.
- Scanned or image-only PDFs are not supported for text retrieval.
- The Skill does not verify certificate, seal, or signature authenticity.
- Ambiguous or missing evidence must be reviewed by humans.
- See [`docs/limitations.md`](docs/limitations.md) for a full list.

## Roadmap

- [x] DOCX and text-layer PDF proposal parsing
- [x] CSV checklist parsing
- [x] Candidate evidence retrieval
- [x] Markdown and CSV report rendering
- [x] PDF page-level provenance in CSV reports
- [x] Embedded PDF image extraction (exhaustive and targeted)
- [x] Optional local PaddleOCR image review
- [ ] Real LLM provider integration
- [ ] Scanned PDF support via OCR
- [ ] DOCX rendered page number mapping
- [ ] Multi-file proposal package support
