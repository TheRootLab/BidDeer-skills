# Image Review Basic Demo Runbook

This runbook describes how to use the image-review synthetic smoke demo with an Agent runtime such as OpenClaw or Hermes.

## Inputs

- Primary runtime input: `inputs/synthetic_image_checklist.csv`
- Human-readable preview: `inputs/synthetic_image_checklist.md`
- Proposal PDF: `inputs/synthetic_image_proposal.pdf`
- Expected output: `expected/expected-output.md`

## Agent Instructions

1. Load `proposal-point-checker/SKILL.md`.
2. Read `inputs/synthetic_image_checklist.csv`.
3. Inspect `inputs/synthetic_image_proposal.pdf`.
4. Produce item-by-item results with:
   - `check_id`
   - `check_item`
   - `status`
   - `evidence_excerpt`
   - `source_location`
   - `notes`
5. Compare the result with `expected/expected-output.md`.

## Required Boundary Checks

The output must not use:

- `pass`
- `fail`
- `rejected`
- `safe`
- `guaranteed`

The output must not claim:

- guaranteed anti-rejection
- automatic bid compliance
- final pass/fail decision
- certificate authenticity verification
- seal authenticity verification
- signature authenticity verification
- risk-level judgment
- bid rejection judgment

Final confirmation must remain with the human reviewer.

## Expected Status Coverage

| Status | Example Check ID |
|---|---|
| `found` | IMG-001, IMG-002, TXT-001 |
| `unclear` | TXT-002 |
| `partially_found` | TXT-003 |
| `not_found` | TXT-004 |

## Image Review Notes

- IMG-001 and IMG-002 require image-based evidence from the embedded service card in Appendix A.
- The Agent runtime may use OCR or image inspection to read the embedded image.
- OCR accuracy varies by runtime and model. This demo does not validate OCR accuracy.
- If the Agent runtime cannot read embedded images, the result for IMG-001 and IMG-002 may differ. Note this in the smoke validation result.

## Synthetic Content

All content in this demo is synthetic. It uses:

- Company: ACME Tech Solutions (fictitious)
- Hotline: 400-000-0000 (synthetic)
- Email: support@example.invalid (synthetic)
- No real company data, certificates, seals, signatures, or personal information.

## Related

- `examples/demos/pdf-basic/` — Text-layer PDF retrieve/report demo runbook.
- `examples/demos/reasoning-status/` — Reasoning status demo runbook.
