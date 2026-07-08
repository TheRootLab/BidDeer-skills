# Picture Review Enhanced Demo Runbook

This runbook describes how to use the enhanced picture-review smoke demo with an Agent runtime such as OpenClaw or Hermes.

## Demo Review Date

**2026-07-08**

Date comparison rule: A certificate obtained date is considered "more than 1 year before the review date" only if it is earlier than or equal to 2025-07-08.

## Inputs

Primary runtime checklist:
- `inputs/enhanced_checklist.csv`

Human-readable checklist preview:
- `inputs/enhanced_checklist.md`

Proposal PDF:
- `inputs/enhanced_proposal.pdf`

Asset map (image field reference):
- `inputs/asset-map.md`

Expected output reference:
- `expected/expected-output.md`

## Agent Instructions

1. Load `proposal-point-checker/SKILL.md`.
2. Read `inputs/enhanced_checklist.csv`.
3. Inspect `inputs/enhanced_proposal.pdf`.
4. Review both text-layer content and embedded image evidence.
5. For picture-based items:
   - Extract visible evidence from images (OCR or image reading).
   - For PIC-001: Extract the registered capital amount and compare against RMB 1,000,000.
   - For PIC-002: Extract the certificate/training date and compare against the 1-year rule relative to 2026-07-08.
   - Keep the human-review boundary explicit.
6. Produce item-by-item results with:
   - `check_id`
   - `check_item`
   - `status`
   - `evidence_excerpt`
   - `source_location`
   - `notes`
7. Compare the result with `expected/expected-output.md`.

## Expected Status Coverage

| Status | Example Check ID |
|---|---|
| `found` | PIC-001, TXT-001 |
| `unclear` | TXT-002 |
| `partially_found` | TXT-003 |
| `not_found` | PIC-002, TXT-004 |

## Required Boundary Checks

The output must not use:

- `pass`
- `fail`
- `rejected`
- `safe`
- `guaranteed`

The output must not claim:

- business license authenticity verification
- certificate authenticity verification
- seal or signature authenticity verification
- automatic legal/compliance judgment
- final bid rejection judgment
- risk-level judgment

Final confirmation must remain with the human reviewer.

## Image Review Notes

- PIC-001 and PIC-002 require image/OCR-based evidence from the embedded images in Appendices A and B.
- The Agent runtime may use OCR or image inspection to read the embedded images.
- OCR accuracy varies by runtime and model. This demo does not validate OCR accuracy.
- If the Agent runtime cannot read embedded images, results for PIC-001 and PIC-002 may differ. Note this in the smoke validation result.

## Synthetic Content

All content in this demo is synthetic. It uses:

- Company: ACME Tech Solutions Co., Ltd. (fictitious)
- USCC: DEMO-91310000-2026-0001 (synthetic)
- Certificate No: DEMO-PM-2026-0001 (synthetic)
- No real business licenses, certificates, seals, signatures, or personal information.

## Related

- `examples/demos/image-review-basic/` — Basic image-review demo runbook.
- `examples/demos/pdf-basic/` — Text-layer PDF retrieve/report demo runbook.
- `examples/demos/reasoning-status/` — Reasoning status demo runbook.
