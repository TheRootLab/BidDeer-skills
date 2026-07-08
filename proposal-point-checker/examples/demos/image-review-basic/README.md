# Image Review Basic Demo

This directory contains a synthetic image-review smoke demo for the `proposal-point-checker` Skill.

## Purpose

This demo is intended for Agent runtime smoke validation. It allows an Agent runtime to verify that:

1. The Skill can load `SKILL.md`.
2. The Agent can read a checklist containing image-review items.
3. The Agent can inspect a synthetic proposal PDF that includes an embedded image.
4. The output remains evidence-based and human-confirmed.
5. The output does not make bid rejection, risk-level, pass/fail, or authenticity judgments.

## What This Demo Does Not Prove

- This demo does not prove OCR accuracy.
- This demo does not make pass/fail, bid rejection, risk-level, or authenticity judgments.
- This demo does not validate scanned-PDF OCR performance.
- Final confirmation remains with the human reviewer.

## Content

| File | Description |
|---|---|
| `inputs/synthetic_image_checklist.csv` | Primary CSV checklist input for runtime smoke validation. |
| `inputs/synthetic_image_checklist.md` | Human-readable checklist preview. |
| `inputs/synthetic_image_proposal.pdf` | Multi-page synthetic proposal PDF with embedded synthetic service card image. |
| `inputs/source-assets/after_sales_card.png` | Synthetic service card image embedded in the PDF. |
| `inputs/source-assets/asset-notes.md` | Notes about the synthetic image asset. |
| `expected/expected-output.md` | Expected item-by-item output for smoke validation. |
| `runbook.md` | Agent runtime runbook for running the demo. |

## Synthetic Content Only

All content in this demo is synthetic. It uses fictitious names, numbers, and entities:

- Company name: ACME Tech Solutions
- Phone: 400-000-0000
- Email: support@example.invalid
- Project name: Synthetic Service Platform
- No real customer documents, company data, certificates, seals, signatures, or personal information.

## Boundaries

This demo follows the Skill boundaries:

- No certificate, seal, or signature authenticity verification.
- No risk-level judgments.
- No bid rejection judgments.
- No pass/fail final decisions.
- No guaranteed anti-rejection claims.
- Human review remains required for final decisions.

## Related

See also:
- `examples/demos/pdf-basic/` — Text-layer PDF retrieve/report demo.
- `examples/demos/reasoning-status/` — Evidence status and reasoning boundary demo.
