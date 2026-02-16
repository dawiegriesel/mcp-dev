from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Configuration for scaffolding a new project."""

    name: str = Field(description="Project name (lowercase, hyphens allowed, e.g. 'my-app')")
    project_type: Literal["work", "personal"] = Field(
        description="'work' deploys to Azure with GitHub Actions; 'personal' deploys to Render.com"
    )
    frontend_type: Literal["react", "htmx"] = Field(
        description="'react' for complex SPAs (Vite + TypeScript); 'htmx' for server-rendered UIs"
    )
    description: str = Field(
        default="",
        description="Short project description for README and package metadata",
    )
    output_dir: str = Field(
        description=(
            "Absolute path to the parent directory where the project folder will be created, "
            "or the target directory itself when use_current_dir is True"
        ),
    )
    use_current_dir: bool = Field(
        default=False,
        description=(
            "When True, scaffold files directly into output_dir instead of "
            "creating a new subdirectory named after the project. "
            "The directory must already exist and be empty."
        ),
    )
    db_name: str | None = Field(
        default=None,
        description="Database name. Defaults to project name with underscores instead of hyphens.",
    )
    include_auth: bool = Field(
        default=True,
        description="Include JWT authentication boilerplate in the API",
    )
    include_alembic: bool = Field(
        default=True,
        description="Include Alembic database migration setup",
    )
    api_port: int = Field(
        default=8000,
        description="Local development API port",
    )
    frontend_port: int = Field(
        default=3000,
        description="Local development frontend port (React only)",
    )
    include_tdd: bool = Field(
        default=False,
        description="Include TDD setup with pytest-cov, factory-boy, and unit/integration test separation",
    )
    include_redis: bool = Field(
        default=False,
        description="Include Redis service in docker-compose for caching and background tasks",
    )
    include_sse: bool = Field(
        default=False,
        description="Include Server-Sent Events endpoint for real-time push updates",
    )

    @property
    def resolved_db_name(self) -> str:
        return self.db_name or self.name.replace("-", "_")

    @property
    def python_package_name(self) -> str:
        return self.name.replace("-", "_")

    @property
    def is_multi_repo(self) -> bool:
        """React projects use 2 repos (api + frontend); HTMX uses 1."""
        return self.frontend_type == "react"


class ComponentConfig(BaseModel):
    """Configuration for adding a component to an existing project."""

    project_dir: str = Field(description="Absolute path to existing project root")
    component: Literal[
        "api_router",
        "db_model",
        "frontend_page",
        "github_action",
        "docker_service",
    ] = Field(description="Type of component to add")
    name: str = Field(description="Name for the new component (e.g., 'products', 'orders')")
    fields: dict[str, str] | None = Field(
        default=None,
        description=(
            "For db_model/api_router: field definitions as {name: type} "
            "e.g. {'title': 'str', 'price': 'float'}"
        ),
    )
