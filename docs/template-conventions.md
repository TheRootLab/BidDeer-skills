# Template Conventions

Each skill MUST define its own input/output contract within its `templates/` directory.

## File Naming

The primary contract should be named `io-contract.md`.

## Content Requirements

1. **Input Schema**: Define exactly what data (and in what format) the skill expects.
2. **Output Schema**: Define exactly what the AI should produce.
3. **Enumerations**: Define status codes or labels (e.g., Evidence status labels, such as 明确证据、疑似证据、冲突证据、未定位到证据、证据不足、无法判断).
4. **Safety Boundaries**: Explicit instructions for the AI to handle sensitive data.

## Why Local Templates?

By keeping templates local to the skill:
1. Skills remain self-contained.
2. Changes to one skill's contract don't break others.
3. It's easier for users to find the specific prompt engineering relevant to the skill.
