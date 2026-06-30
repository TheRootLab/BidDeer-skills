# proposal-point-checker Examples

The public examples are organized by purpose:

- `quickstart/`: Minimal files for first-time users.
- `demos/pdf-basic/`: Full synthetic text-layer PDF demo for the basic retrieve/report workflow.
- `demos/reasoning-status/`: Full synthetic demo for six evidence statuses and the LLM/human reasoning boundary.
- `tools/`: Helper scripts and templates used to generate or integrate example assets.

Each full demo keeps source material under `inputs/` and committed regression artifacts under `expected/`.

All demo files are synthetic and are public demo/reference material. Runtime artifacts should be written to an external task workspace. Do not use the Skill directory as the customer data workspace.

For customer deployment, working-directory, and output-path rules, see [`../docs/runtime-environment.md`](../docs/runtime-environment.md).
