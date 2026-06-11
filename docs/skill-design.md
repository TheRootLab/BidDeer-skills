# Skill Design Principles

Skills in this repository should follow these design principles:

1. **Atomicity:** Each skill should focus on a specific task (e.g., checking proposal evidence against an audit checklist).
2. **De-identification:** Skills should not require or encourage the use of sensitive data in prompts.
3. **Structured Output:** Prefer Markdown or JSON output for easy post-processing.
4. **Contextual Awareness:** Use keywords and schemas to guide the Agent.
5. **Local Templates**: Each skill must include a `templates/io-contract.md` file defining its interaction model.
