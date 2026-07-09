# Expected Output — Picture Review Enhanced Demo

This is the expected output for the enhanced picture-review smoke demo.

Demo review date: **2026-07-08**

The output includes `found`, `partially_found`, `not_found`, and `unclear` statuses. It does not use `pass`, `fail`, `rejected`, `safe`, or `guaranteed`. All image/OCR results require human confirmation.

## Item-by-Item Expected Results

| Check ID | Check Item | Status | Evidence Excerpt | Source Location | Notes |
|---|---|---|---|---|---|
| PIC-001 | 营业执照注册资本 | found | "注册资本：人民币壹佰万元（演示）" | Appendix A / embedded business license image | Visible registered capital is RMB 1,000,000, which satisfies the >= 100万元 threshold. Human review should confirm OCR/image reading. No business license authenticity judgment is made. |
| PIC-002 | 项目管理证书获得日期 | not_found | "培训日期：2026-07-08" | Appendix B / embedded project management training certificate image | The visible training/certificate date is 2026-07-08, which is not more than 1 year before the demo review date 2026-07-08 (threshold: 2025-07-08). It is the same date as the review date. Human review should confirm OCR/date reading. No certificate authenticity judgment is made. |
| TXT-001 | 项目经理任命说明 | found | "The project manager for this project is appointed as Zhang San" | Section 2 | Text evidence found. |
| TXT-002 | 保密承诺 | unclear | "We will follow customer requirements regarding confidential information." | Section 4 | Wording is ambiguous; human review needed. |
| TXT-003 | 培训计划 | partially_found | "Training materials will be provided for end users. Basic operation training will cover system login and core features." | Section 5 | Training materials and basic training are mentioned, but no detailed training plan or schedule is provided. |
| TXT-004 | 交付进度计划 | not_found | — | — | No delivery schedule with milestones was found. A formal delivery schedule is stated as to be coordinated during project planning. |

## Status Coverage

| Status | Check IDs |
|---|---|
| `found` | PIC-001, TXT-001 |
| `partially_found` | TXT-003 |
| `not_found` | PIC-002, TXT-004 |
| `unclear` | TXT-002 |

## Enforced Boundaries

This expected output does **not** use:
- `pass`
- `fail`
- `rejected`
- `safe`
- `guaranteed`

This expected output does **not** claim:
- Business license authenticity verification
- Certificate authenticity verification
- Seal or signature authenticity verification
- Legal or compliance final judgment
- Bid rejection judgment
- Risk-level scoring

Final confirmation remains with the human reviewer.
