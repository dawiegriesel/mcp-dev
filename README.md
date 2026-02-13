# project-scaffold

An MCP server that scaffolds full-stack projects with consistent structure, Docker setup, CI/CD pipelines, and database configuration. Built with [FastMCP](https://github.com/jlowin/fastmcp).

## What it generates

Every scaffolded project comes with:

- **FastAPI** backend with async SQLAlchemy and Pydantic v2
- **PostgreSQL** database with Docker Compose (includes pgAdmin)
- **Frontend** — React (Vite + TypeScript) or HTMX (Tailwind CSS)
- **Alembic** database migrations (optional)
- **JWT authentication** boilerplate (optional)
- **CI/CD** — GitHub Actions for Azure, or Render.com blueprint
- **Makefile** with common dev commands

## Template combinations

| Project type | Frontend | Deploy target | Repo structure |
|---|---|---|---|
| `work` | `react` | Azure (App Service + Static Web Apps) | Multi-repo (API + frontend) |
| `work` | `htmx` | Azure (App Service) | Single repo |
| `personal` | `react` | Render.com | Multi-repo (API + frontend) |
| `personal` | `htmx` | Render.com | Single repo |

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### From GitHub (pip)

```bash
pip install git+https://github.com/dawiegriesel/mcp-dev.git
```

### From GitHub (uv)

```bash
uv pip install git+https://github.com/dawiegriesel/mcp-dev.git
```

### Local development

```bash
git clone https://github.com/dawiegriesel/mcp-dev.git
cd mcp-dev
uv sync
```

For development dependencies (pytest, ruff):

```bash
uv sync --extra dev
```

## Installing the MCP server

### Claude Code

```bash
claude mcp add project-scaffold -- uvx --from "git+https://github.com/dawiegriesel/mcp-dev.git" project-scaffold
```

Or if installed locally:

```bash
claude mcp add project-scaffold -- uv run --directory /path/to/mcp-dev project-scaffold
```

#### Project-scoped config (local development)

This repo includes a `.mcp.json` that registers the server automatically when you open the repo in Claude Code — no manual `claude mcp add` needed. The file uses an absolute path, so you need to update it to match your local clone location:

```json
{
  "mcpServers": {
    "project-scaffold": {
      "command": "uv",
      "args": ["run", "--directory", "/your/local/path/mcp-dev", "project-scaffold"]
    }
  }
}
```

Update the `--directory` value to your actual clone path before using it.

### Claude Desktop

Add this to your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "project-scaffold": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/dawiegriesel/mcp-dev.git",
        "project-scaffold"
      ]
    }
  }
}
```

### Other MCP clients

Run the server with stdio transport (the default):

```bash
project-scaffold
```

Or without installing:

```bash
uvx --from "git+https://github.com/dawiegriesel/mcp-dev.git" project-scaffold
```

## MCP tools

The server exposes five tools via MCP:

### `list_templates`

Returns all available project template combinations and their default stack.

### `create_project`

Scaffolds a complete project. Configuration options:

| Parameter | Required | Default | Description |
|---|---|---|---|
| `name` | yes | — | Project name (lowercase, hyphens allowed) |
| `project_type` | yes | — | `"work"` (Azure) or `"personal"` (Render.com) |
| `frontend_type` | yes | — | `"react"` (SPA) or `"htmx"` (server-rendered) |
| `output_dir` | yes | — | Parent directory for the project folder |
| `description` | no | `""` | Short project description |
| `db_name` | no | derived from name | Database name |
| `include_auth` | no | `true` | Include JWT auth boilerplate |
| `include_alembic` | no | `true` | Include Alembic migrations |
| `api_port` | no | `8000` | Local dev API port |
| `frontend_port` | no | `3000` | Local dev frontend port (React only) |

### `add_component`

Adds a component to an existing scaffolded project. Supported components:

- **`api_router`** — FastAPI router with full CRUD endpoints, plus auto-generated model and schema if fields are provided
- **`db_model`** — SQLAlchemy model with matching Pydantic schemas

Components not yet implemented: `frontend_page`, `github_action`, `docker_service`.

### `validate_project`

Checks that a scaffolded project has all expected files. Reports any missing files.

### `get_project_info`

Reads the `.scaffold.json` metadata from an existing project and returns its configuration.

## Example prompts

Once the MCP server is installed, you can use natural language to scaffold and extend projects. Here are some example prompts to get started:

### Scaffold a new project

> Create a new personal project called "recipe-box" with an HTMX frontend. Put it in ~/projects. Include auth and migrations.

> Scaffold a work project named "inventory-tracker" with a React frontend in ~/work. No auth needed but include Alembic.

> I want to start a new side project called "budget-app". It should be a simple server-rendered app I can deploy to Render. Create it in ~/dev.

> What project templates are available?

### Add components to an existing project

> Add a "products" API router to my project at ~/projects/recipe-box with fields: title (str), prep_time (int), servings (int), instructions (text).

> Add a database model called "category" with fields name (str) and description (text) to ~/projects/recipe-box.

> I need a new "orders" endpoint in my inventory-tracker project. It should have fields for customer_name (str), total (float), and fulfilled (bool).

### Inspect and validate projects

> Check if my project at ~/projects/recipe-box has all the expected files.

> What's the configuration for the project in ~/work/inventory-tracker?

> Validate the project structure at ~/dev/budget-app and tell me if anything is missing.

## Project structure

### React projects (multi-repo)

```
my-app/
├── Makefile
├── README.md
├── .env.example
├── docker-compose.yml
├── docker-compose.override.yml
├── .scaffold.json
├── my-app-api/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── auth/          (optional)
│   ├── alembic/            (optional)
│   ├── tests/
│   └── .github/workflows/
└── my-app-frontend/
    ├── package.json
    ├── vite.config.ts
    ├── Dockerfile
    ├── nginx.conf
    ├── src/
    │   ├── App.tsx
    │   ├── api/
    │   ├── pages/
    │   ├── components/
    │   └── styles/
    └── .github/workflows/
```

### HTMX projects (single repo)

```
my-app/
├── Makefile
├── README.md
├── .env.example
├── docker-compose.yml
├── pyproject.toml
├── Dockerfile
├── .scaffold.json
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── partials/
│   ├── static/css/
│   └── auth/              (optional)
├── alembic/                (optional)
└── tests/
```

## Development

```bash
# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Test
uv run pytest
```

### Automated documentation updates

This repo includes a `docs-pre-commit` Claude agent (`.claude/agents/docs-pre-commit.md`). When working in Claude Code, it triggers automatically before commits to update CHANGELOG.md, README.md, and CLAUDE.md to reflect the changes being committed.

To trigger it manually, tell Claude: "Update the documentation before I commit."

## Architecture

```
src/project_scaffold/
├── __main__.py          # Entry point — runs mcp.run()
├── server.py            # FastMCP server with 5 tool definitions + main()
├── models.py            # Pydantic models (ProjectConfig, ComponentConfig)
├── config.py            # Constants, type maps, template paths
├── generator.py         # Core engine — renders Jinja2 templates to disk
├── renderers/
│   └── api.py           # Component generators (add_router, add_model)
└── templates/           # Jinja2 templates (included in package)
    ├── api/             # FastAPI backend
    ├── frontend/react/  # React + Vite + TypeScript
    ├── frontend/htmx/   # HTMX + Tailwind
    ├── docker/          # Docker Compose
    ├── cicd/azure/      # GitHub Actions for Azure
    ├── cicd/render/     # Render.com blueprint
    ├── alembic/         # Database migrations
    └── common/          # README, Makefile, .env, .gitignore
```
