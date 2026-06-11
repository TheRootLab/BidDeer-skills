# proposal-point-checker

## Purpose

Use this skill to check bid/proposal documents against a user-provided audit checklist.

The skill performs item-by-item evidence positioning, requirement alignment, source tracing, context extraction, and check prompts.

## Required Input

The user should provide:

1. An audit checklist following `templates/io-contract.md`;
2. One or more bid/proposal document excerpts or files.

## Required Output

Always follow `templates/io-contract.md`.

The output must include:

1. A check result summary table;
2. Detailed evidence tables for all non-clear items.

## Evidence Status

Use only the evidence status labels defined in `templates/io-contract.md`.

Do not use simple labels such as `Compliant`, `Non-Compliant`, `Pass`, or `Fail`.

## Boundaries

Do not provide final bidding, legal, compliance, or invalid-bid conclusions.

Do not fabricate file names, page numbers, excerpts, or evidence.

Do not mark a requirement as finally satisfied merely because related evidence was found.

All results are for human review.
