# proposal-point-checker schemas

This directory defines the JSON contracts for the future split-step CLI workflow:

```text
retrieve -> candidates.json -> external reasoning -> judgments.json -> report
```

These schemas are contracts only. Stage 06B does not implement CLI commands, runtime serialization, or provider integrations.

## candidates.json

`candidates.schema.json` describes the output expected from the future `retrieve` step.

The top-level object contains:

- `schemaVersion`: must be `proposal-point-checker.candidates.v0.1`.
- `packages`: an array of evidence packages.

Each package contains:

- `item`: the checklist item with `itemId`, `name`, `requirement`, and `note`.
- `candidates`: candidate evidence fragments for that checklist item.

Each candidate maps to the current `CandidateEvidence` model:

- `blockIndex`
- `userLocator`
- `matchedKeywords`
- `exactText`
- `preContext`
- `postContext`
- `nearbyImages`
- `rowIndex`

`userLocator` is human-facing location context, not a page mapping system. It includes:

- `sourceDocName`
- `headingPath`
- `nearestHeading`
- `nearbyText`
- `locatorHint`
- `evidenceType`

`nearbyImages` records image anchors only. `contentRecognized` must remain `false` in v0.1 because the package does not perform OCR or image content recognition.

## judgments.json

`judgments.schema.json` describes the input expected by the future `report` step after an external Agent or host system has judged the candidate evidence.

The top-level object contains:

- `schemaVersion`: must be `proposal-point-checker.judgments.v0.1`.
- `judgments`: an array of item-level reasoning results.

Each judgment must include:

- `itemId`
- `status`
- `reason`
- `judgmentBasis`
- `manualCheckPrompt`

`status` must be one of:

- `CLEAR_EVIDENCE`
- `SUSPECTED_EVIDENCE`
- `CONFLICTING_EVIDENCE`
- `NOT_FOUND`
- `INSUFFICIENT_EVIDENCE`
- `UNABLE_TO_JUDGE`

`referencedEvidenceIndices` is optional. It can point to candidate indices from the matching package in `candidates.json`, but it does not replace `judgmentBasis` or `manualCheckPrompt`.

## External Agent Responsibilities

An external Agent or host system may:

1. Read `candidates.json`.
2. Review each package's checklist item and candidate evidence.
3. Produce exactly one judgment for each checklist `itemId`.
4. Write `judgments.json` that validates against `judgments.schema.json`.

The external reasoner must not:

- Add provider-specific fields such as `provider`, `model`, `apiKey`, `temperature`, or `promptTemplate`.
- Add PDF, OCR, image text, or page mapping fields.
- Convert `EvidenceStatus` into pass/fail, risk level, bid rejection, or final compliance conclusions.

## v0.1 Boundary

The schemas intentionally avoid:

- `page_hint`
- `renderedPageNum`
- PDF location metadata
- OCR text
- image content text
- real LLM provider configuration

The only supported image information is nearby image-anchor metadata already produced by the DOCX parser.
