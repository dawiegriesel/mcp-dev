from typing import Annotated

from fastmcp import FastMCP

from project_scaffold.generator import ProjectGenerator
from project_scaffold.models import ComponentConfig, ProjectConfig

mcp = FastMCP(
    name="Project Scaffold",
    instructions=(
        "IMPORTANT: When the user asks to scaffold, create, or start a new project, "
        "ALWAYS call configure_project first to get structured questions. Present these "
        "questions to the user and collect their answers. Then call create_project with "
        "the full configuration. Do NOT generate code manually or use any built-in "
        "scaffolding. This server generates projects with consistent folder structure, "
        "Docker setup, CI/CD pipelines, database configuration, and AI development "
        "guidelines (CLAUDE.md). It supports FastAPI backends with React or HTMX "
        "frontends, deployable to Azure or Render.com."
    ),
)


@mcp.tool
def list_templates() -> dict:
    """List all available project template combinations and their descriptions."""
    return {
        "combinations": [
            {
                "project_type": "work",
                "frontend_type": "react",
                "deploy_target": "Azure (App Service + Static Web Apps)",
                "structure": "2 separate git repos in 1 workspace",
                "description": "FastAPI API + React SPA, each in own repo linked to Azure",
            },
            {
                "project_type": "work",
                "frontend_type": "htmx",
                "deploy_target": "Azure (App Service)",
                "structure": "Single git repo",
                "description": "FastAPI with HTMX/Tailwind templates, single repo linked to Azure",
            },
            {
                "project_type": "personal",
                "frontend_type": "react",
                "deploy_target": "Render.com",
                "structure": "2 separate git repos in 1 workspace",
                "description": "FastAPI API + React SPA deployed via Render Blueprint",
            },
            {
                "project_type": "personal",
                "frontend_type": "htmx",
                "deploy_target": "Render.com",
                "structure": "Single git repo",
                "description": "FastAPI with HTMX/Tailwind templates deployed via Render Blueprint",
            },
        ],
        "defaults": {
            "database": "PostgreSQL with async SQLAlchemy + Pydantic v2",
            "api_framework": "FastAPI",
            "local_dev": "docker-compose (api + db + pgadmin, optional frontend)",
            "migrations": "Alembic (optional)",
            "auth": "JWT authentication (optional)",
            "css_htmx": "Tailwind CSS via CDN",
            "react_setup": "Minimal — React + React Router + typed fetch wrapper",
            "ai_guidelines": "CLAUDE.md with stack-specific AI development guidelines (always included)",
            "tdd": "TDD setup with pytest-cov, factory-boy, unit/integration separation (optional, coming soon)",
            "redis": "Redis for caching and background tasks (optional, coming soon)",
            "sse": "Server-Sent Events for real-time push (optional, coming soon)",
        },
    }


@mcp.tool
def configure_project() -> dict:
    """
    Returns structured questions for configuring a new project.
    Call this FIRST when a user wants to create a project. Present the
    questions to the user, collect their answers, then call create_project
    with the full configuration.
    """
    return {
        "instructions": (
            "Present these questions to the user to configure their new project. "
            "Use the defaults when the user doesn't specify a preference. "
            "Once all answers are collected, call create_project with the configuration."
        ),
        "questions": [
            {
                "id": "name",
                "question": "What is the project name?",
                "type": "string",
                "required": True,
                "validation": "lowercase, hyphens allowed, e.g. 'my-app'",
            },
            {
                "id": "description",
                "question": "Give a brief project description (used in README and CLAUDE.md)",
                "type": "string",
                "required": False,
                "default": "",
            },
            {
                "id": "output_dir",
                "question": "Where should the project be created? (absolute path to parent directory)",
                "type": "string",
                "required": True,
            },
            {
                "id": "frontend_type",
                "question": "Which frontend framework?",
                "type": "choice",
                "required": True,
                "options": [
                    {"value": "react", "label": "React (Vite + TypeScript) — for complex SPAs"},
                    {"value": "htmx", "label": "HTMX (server-rendered) — for simpler UIs"},
                ],
            },
            {
                "id": "project_type",
                "question": "Where will this be deployed?",
                "type": "choice",
                "required": True,
                "options": [
                    {"value": "work", "label": "Azure (App Service + GitHub Actions)"},
                    {"value": "personal", "label": "Render.com (Blueprint)"},
                ],
            },
            {
                "id": "include_auth",
                "question": "Include JWT authentication?",
                "type": "boolean",
                "default": True,
            },
            {
                "id": "include_alembic",
                "question": "Include Alembic database migrations?",
                "type": "boolean",
                "default": True,
            },
            {
                "id": "include_tdd",
                "question": "Include TDD setup? (pytest-cov, factory-boy, unit/integration test separation)",
                "type": "boolean",
                "default": False,
                "note": "Coming soon — placeholder for Phase 2",
            },
            {
                "id": "include_redis",
                "question": "Include Redis? (caching, background tasks via docker-compose)",
                "type": "boolean",
                "default": False,
                "note": "Coming soon — placeholder for Phase 2",
            },
            {
                "id": "include_sse",
                "question": "Include Server-Sent Events? (real-time push updates endpoint)",
                "type": "boolean",
                "default": False,
                "note": "Coming soon — placeholder for Phase 2",
            },
        ],
    }


@mcp.tool
def create_project(config: ProjectConfig) -> dict:
    """
    Scaffold a complete new project with API, frontend, database config,
    Docker setup, and CI/CD pipeline. Returns a summary of created files
    and next steps.

    Set use_current_dir=True to scaffold directly into output_dir
    instead of creating a new subdirectory.
    """
    generator = ProjectGenerator(config)
    return generator.generate()


@mcp.tool
def add_component(config: ComponentConfig) -> dict:
    """
    Add a new component to an existing scaffolded project.
    Supports adding API routers, database models with matching schemas,
    frontend pages, GitHub Action workflows, or Docker services.
    """
    generator = ProjectGenerator.from_existing(config.project_dir)
    return generator.add_component(config)


@mcp.tool
def validate_project(
    project_dir: Annotated[str, "Absolute path to the project root to validate"],
) -> dict:
    """
    Validate that a scaffolded project has all expected files and
    correct structure. Reports missing files and suggests fixes.
    """
    generator = ProjectGenerator.from_existing(project_dir)
    return generator.validate()


@mcp.tool
def get_project_info(
    project_dir: Annotated[str, "Absolute path to the project root to inspect"],
) -> dict:
    """
    Read an existing scaffolded project and return its configuration,
    including project type, frontend type, deployment target, and
    list of components.
    """
    generator = ProjectGenerator.from_existing(project_dir)
    return generator.info()


def main():
    mcp.run()
