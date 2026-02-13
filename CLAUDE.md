# CLAUDE.md

## Project overview

MCP server that scaffolds full-stack projects (FastAPI + React/HTMX) with Docker, CI/CD, and database config. Built with FastMCP + Jinja2. Installable as a Python package from GitHub.

## Commands

```bash
# Run the MCP server
uv run project-scaffold

# Install dependencies
uv sync              # production
uv sync --extra dev  # with pytest + ruff

# Lint and format
uv run ruff check src/
uv run ruff format src/

# Run tests
uv run pytest
```

## Architecture

- `src/project_scaffold/server.py` — FastMCP server, defines 5 MCP tools + `main()` entry point
- `src/project_scaffold/models.py` — Pydantic models: `ProjectConfig`, `ComponentConfig`
- `src/project_scaffold/config.py` — Constants (template dir, type maps, defaults)
- `src/project_scaffold/generator.py` — Core engine: `ProjectGenerator` class renders Jinja2 templates to disk
- `src/project_scaffold/renderers/api.py` — Component generators for `add_router` and `add_model`
- `src/project_scaffold/templates/` — Jinja2 templates organized by category (api, frontend, docker, cicd, alembic, common)

## Key patterns

- All templates receive a context dict built by `ProjectGenerator._context()` with keys: `project_name`, `project_type`, `frontend_type`, `description`, `db_name`, `db_user`, `db_password`, `include_auth`, `include_alembic`, `api_port`, `frontend_port`, `is_multi_repo`, `python_package_name`
- React projects are multi-repo (separate `{name}-api/` and `{name}-frontend/` dirs). HTMX projects are single-repo.
- `.scaffold.json` metadata file is written to project root and used by `from_existing()` to reload config
- Type maps in `config.py` translate user-friendly types (str, int, float, bool, etc.) to SQLAlchemy and Pydantic types
- Component generators in `renderers/api.py` produce Python code as strings (not templates)
- Templates live inside the package (`src/project_scaffold/templates/`) so they're included in pip installs

## Code style

- Python 3.12+, Ruff with 100-char line length
- Pydantic v2 models with `Field(description=...)`
- Type annotations throughout, `from __future__ import annotations` in most files
- `TYPE_CHECKING` guard for circular imports in renderers

## Template structure

Templates are `.j2` Jinja2 files under `src/project_scaffold/templates/`. Main categories:
- `api/` — FastAPI app (models, schemas, routers, auth, tests)
- `frontend/react/` — Vite + TypeScript + React Router
- `frontend/htmx/` — Server-rendered HTML with HTMX + Tailwind CDN
- `docker/` — docker-compose.yml files
- `cicd/azure/` — GitHub Actions for Azure
- `cicd/render/` — render.yaml blueprint
- `alembic/` — Migration config
- `common/` — README, Makefile, .env.example, .gitignore
