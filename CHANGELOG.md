# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.3.2] — 2026-02-16

### Fixed

- Fix Jinja2 whitespace in Makefile template — blank lines between targets and recipes broke `make` commands
- Fix Jinja2 whitespace in docker-compose, render.yaml, and Azure CI/CD YAML templates — spurious blank lines broke YAML structure
- Fix API Dockerfile — copy `app/` source into builder stage so hatchling can build the wheel
- Fix `pyproject.toml` template — add `[tool.hatch.build.targets.wheel] packages = ["app"]` so hatchling finds the app package
- Fix `pyproject.toml` template — remove blank lines from Jinja2 conditionals in dependency lists
- Fix React frontend Dockerfile — use `npm install` fallback when `package-lock.json` doesn't exist (scaffolded projects have no lockfile)
- Fix `docker-compose.override.yml` template — use Dockerfile `target: builder` for frontend dev so npm is available (production image is nginx-based)

## [0.3.1] — 2026-02-16

### Added

- `docs-pre-commit` Claude agent (`.claude/agents/docs-pre-commit.md`) — automatically updates CHANGELOG, README, and other docs before commits
- MIT license (`LICENSE` and `pyproject.toml`)
- `CODE_OF_CONDUCT.md` — Contributor Covenant Code of Conduct
- `CONTRIBUTING.md` — contribution guidelines
- Alpha notice in README

### Changed

- Remove `.mcp.json` from version control and add to `.gitignore` to avoid leaking local paths — README now instructs users to create their own
- Repository is now public
- Replace `python-jose` with `PyJWT` in generated projects — `python-jose` is unmaintained

### Fixed

- Add duplicate email check to HTMX user creation form — previously crashed with IntegrityError on duplicate
- Add authorization checks to user update/delete endpoints — users can now only modify their own account
- Add secret key validation in generated config — rejects default `change-me-in-production` value in non-development environments

## [0.3.0] — 2026-02-13

### Changed

- Restructure repo as an installable Python package under `src/project_scaffold/`
- Move entry point to `project-scaffold` console script via `pyproject.toml`
- Templates are now bundled inside the package and included in pip installs

## [0.2.0] — 2026-02-13

### Fixed

- Multiple bugs across scaffold templates (auth routes, Alembic config, Docker Compose env vars)

## [0.1.0] — 2026-02-13

### Added

- Initial release: FastMCP-based MCP server with five tools (`list_templates`, `create_project`, `add_component`, `validate_project`, `get_project_info`)
- Jinja2 templates for FastAPI + React (Vite/TypeScript) and HTMX frontends
- Docker Compose setup with pgAdmin
- CI/CD templates for Azure (GitHub Actions) and Render.com
- Optional JWT auth and Alembic migration boilerplate
