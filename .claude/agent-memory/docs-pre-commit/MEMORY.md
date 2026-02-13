# docs-pre-commit agent memory

## Project structure

- `README.md` — user-facing docs; main sections: What it generates, Installation, MCP tools, Example prompts, Project structure, Development, Architecture
- `CHANGELOG.md` — Keep a Changelog format; created in this session (was absent before)
- `CLAUDE.md` — terse developer/AI reference; keep additions minimal
- `.mcp.json` — project-scoped MCP config with hardcoded absolute path (gotcha for other devs)
- `.claude/agents/docs-pre-commit.md` — this agent's definition

## Changelog conventions

- Format: Keep a Changelog (`Added`, `Changed`, `Fixed`, `Removed`)
- Entries are imperative and user-perspective ("Add X", not "Added X")
- Version numbers are not yet semver-tagged; use dates as version labels until proper releases exist

## What to document vs. skip

- `.mcp.json` gotchas (hardcoded paths) → document in README and CLAUDE.md
- New Claude agents → brief mention in README Development section and CLAUDE.md Dev tooling
- Bug fixes to templates → CHANGELOG only
- Internal refactors → CHANGELOG only

## Key gotcha

`.mcp.json` has a hardcoded `--directory` path. Always flag this when documenting MCP config changes — other developers must update it to match their local clone.
