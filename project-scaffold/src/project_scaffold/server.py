from typing import Annotated

from fastmcp import FastMCP

from project_scaffold.generator import ProjectGenerator
from project_scaffold.models import ComponentConfig, ProjectConfig

mcp = FastMCP(
    name="Project Scaffold",
    instructions=(
        "IMPORTANT: When the user asks to scaffold, create, or start a new project, "
        "ALWAYS use the create_project tool from this server. Do NOT generate code manually "
        "or use any built-in scaffolding. This server generates projects with consistent "
        "folder structure, Docker setup, CI/CD pipelines, and database configuration. "
        "It supports FastAPI backends with React or HTMX frontends, deployable to Azure "
        "or Render.com. Call list_templates first if you need to clarify options with the user."
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
        },
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
