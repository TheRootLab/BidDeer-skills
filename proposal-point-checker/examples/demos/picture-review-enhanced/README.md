# Picture Review Enhanced Demo

This directory contains an enhanced synthetic picture-review demo for the `proposal-point-checker` Skill.

## Purpose

This demo is intended for Agent runtime smoke validation. It allows an Agent runtime to verify that:

1. The Skill can load `SKILL.md`.
2. The Agent can read a checklist containing picture-review items with numeric and date comparison rules.
3. The Agent can inspect a synthetic proposal PDF with embedded business license and training certificate images.
4. The Agent can extract visible text from images and apply comparison rules:
   - PIC-001: Registered capital >= RMB 1,000,000 (numeric comparison)
   - PIC-002: Certificate date more than 1 year before 2026-07-08 (date comparison)
5. The output remains evidence-based and human-confirmed.
6. The output does not make bid rejection, risk-level, pass/fail, or authenticity judgments.

## Demo Review Date

The fixed demo review date is **2026-07-08**.

For PIC-002, the certificate obtained date must be earlier than or equal to 2025-07-08 to satisfy the "more than 1 year" rule.

## What This Demo Does Not Prove

- This demo does not prove OCR accuracy.
- This demo does not verify business license authenticity.
- This demo does not verify certificate authenticity.
- This demo does not verify seal or signature authenticity.
- This demo does not make pass/fail, bid rejection, risk-level, or authenticity judgments.
- Final confirmation remains with the human reviewer.

## Content

| File | Description |
|---|---|
| `inputs/enhanced_checklist.csv` | Primary CSV checklist input for runtime smoke validation. |
| `inputs/enhanced_checklist.md` | Human-readable checklist preview. |
| `inputs/enhanced_proposal.pdf` | Multi-page synthetic proposal PDF with embedded business license and training certificate images. |
| `inputs/asset-map.md` | Maps source images to their purpose and visible fields. |
| `expected/expected-output.md` | Expected item-by-item output for smoke validation. |
| `runbook.md` | Agent runtime runbook for running the demo. |

## Source Images

The embedded images are sourced from:

- `examples/demos/pictures/bli.png` — Synthetic business license image
- `examples/demos/pictures/PM.png` — Synthetic project management training certificate image

All images are synthetic/demo only. See `inputs/asset-map.md` for detailed field mappings.

## Synthetic Content Only

All content in this demo is synthetic. It uses fictitious names, numbers, and entities:

- Company name: ACME Tech Solutions Co., Ltd.
- USCC: DEMO-91310000-2026-0001
- Certificate No: DEMO-PM-2026-0001
- No real business licenses, certificates, seals, signatures, or personal information.

## Boundaries

This demo follows the Skill boundaries:

- No business license authenticity verification.
- No certificate authenticity verification.
- No seal or signature authenticity verification.
- No risk-level judgments.
- No bid rejection judgments.
- No pass/fail final decisions.
- Human review remains required for final decisions.

## Related

See also:
- `examples/demos/image-review-basic/` — Basic image-review demo with service card image.
- `examples/demos/pdf-basic/` — Text-layer PDF retrieve/report demo.
- `examples/demos/reasoning-status/` — Evidence status and reasoning boundary demo.
