# Quickstart Examples

This directory contains the smallest user-facing example:

- `sample_checklist.csv` is the minimal checklist used by the current CLI quickstart.
- `sample_proposal.docx` is generated locally and is not committed.
- `sample_checklist.md`, `sample_proposal_excerpt.txt`, and `sample_output.md` are legacy static reference snapshots; they are not current CLI regression outputs.

Generate the synthetic DOCX from the Skill root:

```bash
python examples/tools/generate_sample_docx.py examples/quickstart/sample_proposal.docx
```

Run deterministic candidate retrieval and write the output to an external task workspace:

```bash
python -m biddeer_checker.cli retrieve \
  --csv "examples/quickstart/sample_checklist.csv" \
  --proposal "examples/quickstart/sample_proposal.docx" \
  --out "<absolute_task_workspace>/quickstart_candidates.json"
```

This quickstart is not a full reasoning demo. Use `examples/demos/pdf-basic/` for the complete text-layer PDF workflow and `examples/demos/reasoning-status/` for the six-status reasoning demo.
