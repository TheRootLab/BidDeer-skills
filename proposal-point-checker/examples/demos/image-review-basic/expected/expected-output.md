# Expected Output — Image Review Basic Demo

This is the expected output for the synthetic image-review smoke demo.

The output includes `found`, `partially_found`, `not_found`, and `unclear` statuses.

It does not use `pass`, `fail`, `rejected`, `safe`, or `guaranteed`.

All image/OCR results require human confirmation. OCR is not claimed as perfect or final.

## Item-by-Item Expected Results

| Check ID | Check Item | Status | Evidence Excerpt | Source Location | Notes |
|---|---|---|---|---|---|
| IMG-001 | After-sales hotline card | found | "Hotline: 400-000-0000" | Appendix A / embedded image | Evidence appears in the synthetic service card image. Human review should confirm OCR/image reading. |
| IMG-002 | Service hours in image | found | "Service Hours: 7x24" | Appendix A / embedded image | Evidence appears in the synthetic service card image. Human review should confirm OCR/image reading. |
| TXT-001 | Project manager appointment | found | "The project manager for this project is appointed as Zhang Wei" | Section 2 | Text evidence found. |
| TXT-002 | Confidentiality commitment | unclear | "We will follow customer requirements regarding confidential information." | Section 4 | Wording is ambiguous; human review needed. |
| TXT-003 | Training plan | partially_found | "Training materials will be provided." | Section 5 | Training materials are mentioned, but no detailed training plan or schedule is provided. |
| TXT-004 | Delivery schedule | not_found | — | — | No delivery schedule with milestones was found. |
