from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from project_scaffold.config import (
    DEFAULT_DB_PASSWORD,
    DEFAULT_DB_USER,
    SCAFFOLD_METADATA_FILE,
    TEMPLATES_DIR,
)
from project_scaffold.models import ComponentConfig, ProjectConfig


class ProjectGenerator:
    """Core engine: reads Jinja2 templates, renders them, writes output files."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        if config.use_current_dir:
            self.project_root = Path(config.output_dir)
        else:
            self.project_root = Path(config.output_dir) / config.name
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(default_for_string=False, default=False),
            keep_trailing_newline=True,
        )
        self.files_created: list[str] = []

    @classmethod
    def from_existing(cls, project_dir: str) -> ProjectGenerator:
        """Load a generator from an existing scaffolded project's metadata."""
        meta_path = Path(project_dir) / SCAFFOLD_METADATA_FILE
        if not meta_path.exists():
            raise FileNotFoundError(
                f"No {SCAFFOLD_METADATA_FILE} found in {project_dir}. Is this a scaffolded project?"
            )
        meta = json.loads(meta_path.read_text())
        use_current_dir = meta.get("use_current_dir", False)
        config = ProjectConfig(
            name=meta["project_name"],
            project_type=meta["project_type"],
            frontend_type=meta["frontend_type"],
            description=meta.get("description", ""),
            output_dir=str(project_dir) if use_current_dir else str(Path(project_dir).parent),
            db_name=meta.get("db_name"),
            include_auth=meta.get("include_auth", True),
            include_alembic=meta.get("include_alembic", True),
            api_port=meta.get("api_port", 8000),
            frontend_port=meta.get("frontend_port", 3000),
            use_current_dir=use_current_dir,
            include_tdd=meta.get("include_tdd", False),
            include_redis=meta.get("include_redis", False),
            include_sse=meta.get("include_sse", False),
        )
        return cls(config)

    def _context(self) -> dict:
        """Build the Jinja2 template context from config."""
        return {
            "project_name": self.config.name,
            "project_type": self.config.project_type,
            "frontend_type": self.config.frontend_type,
            "description": self.config.description,
            "db_name": self.config.resolved_db_name,
            "db_user": DEFAULT_DB_USER,
            "db_password": DEFAULT_DB_PASSWORD,
            "include_auth": self.config.include_auth,
            "include_alembic": self.config.include_alembic,
            "api_port": self.config.api_port,
            "frontend_port": self.config.frontend_port,
            "is_multi_repo": self.config.is_multi_repo,
            "python_package_name": self.config.python_package_name,
            "include_tdd": self.config.include_tdd,
            "include_redis": self.config.include_redis,
            "include_sse": self.config.include_sse,
        }

    def _render(self, template_path: str, context: dict | None = None) -> str:
        """Render a single Jinja2 template."""
        ctx = self._context()
        if context:
            ctx.update(context)
        template = self.env.get_template(template_path)
        return template.render(ctx)

    def _write(self, output_path: Path, content: str) -> None:
        """Write rendered content to a file, creating parent dirs as needed."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        self.files_created.append(str(output_path.relative_to(self.project_root)))

    def _write_empty(self, output_path: Path) -> None:
        """Create an empty file (e.g. __init__.py, .gitkeep)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        self.files_created.append(str(output_path.relative_to(self.project_root)))

    def _api_root(self) -> Path:
        """Get the API directory root, depending on project structure."""
        if self.config.is_multi_repo:
            return self.project_root / f"{self.config.name}-api"
        return self.project_root

    def _frontend_root(self) -> Path:
        """Get the frontend directory root (React projects only)."""
        return self.project_root / f"{self.config.name}-frontend"

    def generate(self) -> dict:
        """Generate the complete project. Returns summary."""
        if self.config.use_current_dir:
            if not self.project_root.exists():
                return {
                    "status": "error",
                    "message": f"Directory does not exist: {self.project_root}",
                }
            if any(self.project_root.iterdir()):
                return {
                    "status": "error",
                    "message": (
                        f"Directory is not empty: {self.project_root}. "
                        "use_current_dir requires an empty directory."
                    ),
                }
        else:
            if self.project_root.exists():
                return {
                    "status": "error",
                    "message": f"Directory already exists: {self.project_root}",
                }
            self.project_root.mkdir(parents=True)

        ctx = self._context()

        # Common workspace files
        self._generate_common()

        # Docker files (at workspace root)
        self._generate_docker()

        # API
        self._generate_api()

        # Frontend (React only — HTMX templates are inside the API)
        if self.config.frontend_type == "react":
            self._generate_react_frontend()
        else:
            self._generate_htmx_templates()

        # CI/CD
        if self.config.project_type == "work":
            self._generate_azure_cicd()
        else:
            self._generate_render_config()

        # Alembic
        if self.config.include_alembic:
            self._generate_alembic()

        # Auth
        if self.config.include_auth:
            self._generate_auth()

        # AI development guidelines
        self._generate_claude()

        # Scaffold metadata
        self._write_metadata()

        # Init git repos
        git_instructions = self._git_instructions()

        return {
            "status": "success",
            "project_root": str(self.project_root),
            "files_created": len(self.files_created),
            "file_list": self.files_created,
            "next_steps": git_instructions,
        }

    def _generate_common(self) -> None:
        """Generate workspace-level common files."""
        ctx = self._context()
        for tmpl, out in [
            ("common/README.md.j2", "README.md"),
            ("common/env_example.j2", ".env.example"),
            ("common/Makefile.j2", "Makefile"),
        ]:
            self._write(self.project_root / out, self._render(tmpl))

        # .gitignore goes into each repo root, not workspace root for multi-repo
        gitignore_content = self._render("common/gitignore.j2")
        if self.config.is_multi_repo:
            self._write(self._api_root() / ".gitignore", gitignore_content)
            self._write(
                self._frontend_root() / ".gitignore", self._render("common/gitignore_frontend.j2")
            )
        else:
            self._write(self.project_root / ".gitignore", gitignore_content)

    def _generate_docker(self) -> None:
        """Generate docker-compose files at workspace root."""
        for tmpl, out in [
            ("docker/docker-compose.yml.j2", "docker-compose.yml"),
            ("docker/docker-compose.override.yml.j2", "docker-compose.override.yml"),
        ]:
            self._write(self.project_root / out, self._render(tmpl))

    def _generate_api(self) -> None:
        """Generate the FastAPI application."""
        api_root = self._api_root()
        app_dir = api_root / "app"

        # Root API files
        for tmpl, out in [
            ("api/pyproject.toml.j2", "pyproject.toml"),
            ("api/Dockerfile.j2", "Dockerfile"),
            ("api/startup.sh.j2", "startup.sh"),
        ]:
            self._write(api_root / out, self._render(tmpl))

        # App module files
        for tmpl, out in [
            ("api/app/main.py.j2", "main.py"),
            ("api/app/config.py.j2", "config.py"),
            ("api/app/database.py.j2", "database.py"),
            ("api/app/dependencies.py.j2", "dependencies.py"),
        ]:
            self._write(app_dir / out, self._render(tmpl))

        self._write_empty(app_dir / "__init__.py")

        # Models
        models_dir = app_dir / "models"
        self._write_empty(models_dir / "__init__.py")
        for tmpl, out in [
            ("api/app/models/base.py.j2", "base.py"),
            ("api/app/models/user.py.j2", "user.py"),
        ]:
            self._write(models_dir / out, self._render(tmpl))

        # Schemas
        schemas_dir = app_dir / "schemas"
        self._write_empty(schemas_dir / "__init__.py")
        for tmpl, out in [
            ("api/app/schemas/common.py.j2", "common.py"),
            ("api/app/schemas/user.py.j2", "user.py"),
        ]:
            self._write(schemas_dir / out, self._render(tmpl))

        # Routers
        routers_dir = app_dir / "routers"
        self._write_empty(routers_dir / "__init__.py")
        for tmpl, out in [
            ("api/app/routers/health.py.j2", "health.py"),
            ("api/app/routers/users.py.j2", "users.py"),
        ]:
            self._write(routers_dir / out, self._render(tmpl))

        if self.config.include_sse:
            self._write(routers_dir / "sse.py", self._render("api/app/routers/sse.py.j2"))

        # Tests
        tests_dir = api_root / "tests"
        self._write_empty(tests_dir / "__init__.py")
        for tmpl, out in [
            ("api/tests/conftest.py.j2", "conftest.py"),
            ("api/tests/test_health.py.j2", "test_health.py"),
        ]:
            self._write(tests_dir / out, self._render(tmpl))

    def _generate_react_frontend(self) -> None:
        """Generate the React (Vite + TypeScript) frontend."""
        fe_root = self._frontend_root()
        src_dir = fe_root / "src"

        for tmpl, out in [
            ("frontend/react/package.json.j2", "package.json"),
            ("frontend/react/vite.config.ts.j2", "vite.config.ts"),
            ("frontend/react/tsconfig.json.j2", "tsconfig.json"),
            ("frontend/react/tsconfig.node.json.j2", "tsconfig.node.json"),
            ("frontend/react/index.html.j2", "index.html"),
            ("frontend/react/Dockerfile.j2", "Dockerfile"),
            ("frontend/react/nginx.conf.j2", "nginx.conf"),
        ]:
            self._write(fe_root / out, self._render(tmpl))

        for tmpl, out in [
            ("frontend/react/src/main.tsx.j2", "main.tsx"),
            ("frontend/react/src/App.tsx.j2", "App.tsx"),
            ("frontend/react/src/vite-env.d.ts.j2", "vite-env.d.ts"),
        ]:
            self._write(src_dir / out, self._render(tmpl))

        # API client
        self._write(
            src_dir / "api" / "client.ts",
            self._render("frontend/react/src/api/client.ts.j2"),
        )

        # Pages and components
        self._write(
            src_dir / "pages" / "Home.tsx",
            self._render("frontend/react/src/pages/Home.tsx.j2"),
        )
        self._write(
            src_dir / "components" / "Layout.tsx",
            self._render("frontend/react/src/components/Layout.tsx.j2"),
        )

        # Styles
        self._write(
            src_dir / "styles" / "globals.css",
            self._render("frontend/react/src/styles/globals.css.j2"),
        )

        # Public
        (fe_root / "public").mkdir(parents=True, exist_ok=True)

    def _generate_htmx_templates(self) -> None:
        """Generate HTMX templates inside the API app directory."""
        api_root = self._api_root()
        templates_dir = api_root / "app" / "templates"
        static_dir = api_root / "app" / "static"

        for tmpl, out in [
            ("frontend/htmx/templates/base.html.j2", "base.html"),
            ("frontend/htmx/templates/index.html.j2", "index.html"),
        ]:
            self._write(templates_dir / out, self._render(tmpl))

        # Partials directory
        self._write(
            templates_dir / "partials" / "user_list.html",
            self._render("frontend/htmx/templates/partials/user_list.html.j2"),
        )
        self._write(
            templates_dir / "partials" / "user_form.html",
            self._render("frontend/htmx/templates/partials/user_form.html.j2"),
        )

        # Static files
        self._write(
            static_dir / "css" / "style.css",
            self._render("frontend/htmx/static/css/style.css.j2"),
        )

        # Pages router for HTMX
        self._write(
            api_root / "app" / "routers" / "pages.py",
            self._render("api/app/routers/pages.py.j2"),
        )

    def _generate_azure_cicd(self) -> None:
        """Generate GitHub Actions workflows for Azure deployment."""
        api_root = self._api_root()
        api_workflows = api_root / ".github" / "workflows"

        self._write(
            api_workflows / "ci.yml",
            self._render("cicd/azure/ci-api.yml.j2"),
        )

        if self.config.frontend_type == "react":
            fe_root = self._frontend_root()
            fe_workflows = fe_root / ".github" / "workflows"
            self._write(
                fe_workflows / "ci.yml",
                self._render("cicd/azure/ci-frontend.yml.j2"),
            )
            self._write(
                fe_workflows / "deploy.yml",
                self._render("cicd/azure/deploy-frontend.yml.j2"),
            )

    def _generate_render_config(self) -> None:
        """Generate render.yaml for Render.com deployment."""
        self._write(
            self.project_root / "render.yaml",
            self._render("cicd/render/render.yaml.j2"),
        )

    def _generate_alembic(self) -> None:
        """Generate Alembic migration configuration."""
        api_root = self._api_root()
        alembic_dir = api_root / "alembic"

        self._write(api_root / "alembic.ini", self._render("alembic/alembic.ini.j2"))
        self._write(alembic_dir / "env.py", self._render("alembic/env.py.j2"))
        self._write(
            alembic_dir / "script.py.mako",
            (TEMPLATES_DIR / "alembic" / "script.py.mako").read_text(),
        )
        self._write_empty(alembic_dir / "versions" / ".gitkeep")

    def _generate_auth(self) -> None:
        """Generate JWT authentication boilerplate."""
        api_root = self._api_root()
        auth_dir = api_root / "app" / "auth"

        self._write_empty(auth_dir / "__init__.py")
        self._write(auth_dir / "jwt.py", self._render("api/app/auth/jwt.py.j2"))
        self._write(auth_dir / "routes.py", self._render("api/app/auth/routes.py.j2"))

    def _generate_claude(self) -> None:
        """Generate CLAUDE.md with AI development guidelines at project root."""
        self._write(
            self.project_root / "CLAUDE.md",
            self._render("claude/CLAUDE.md.j2"),
        )

    def _write_metadata(self) -> None:
        """Write .scaffold.json metadata."""
        meta = {
            "scaffold_version": "0.1.0",
            "project_name": self.config.name,
            "project_type": self.config.project_type,
            "frontend_type": self.config.frontend_type,
            "description": self.config.description,
            "db_name": self.config.resolved_db_name,
            "include_auth": self.config.include_auth,
            "include_alembic": self.config.include_alembic,
            "api_port": self.config.api_port,
            "frontend_port": self.config.frontend_port,
            "use_current_dir": self.config.use_current_dir,
            "include_tdd": self.config.include_tdd,
            "include_redis": self.config.include_redis,
            "include_sse": self.config.include_sse,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "components": [],
        }
        path = self.project_root / SCAFFOLD_METADATA_FILE
        self._write(path, json.dumps(meta, indent=2) + "\n")

    def _git_instructions(self) -> list[str]:
        """Return next-step instructions for the user."""
        steps = []
        if self.config.is_multi_repo:
            api_name = f"{self.config.name}-api"
            fe_name = f"{self.config.name}-frontend"
            steps.append(f"cd {self.project_root / api_name} && git init")
            steps.append(f"cd {self.project_root / fe_name} && git init")
        else:
            if self.config.use_current_dir:
                steps.append("git init")
            else:
                steps.append(f"cd {self.project_root} && git init")

        steps.append(f"Copy .env.example to .env and fill in values")
        steps.append(f"Run 'make up' to start docker-compose")
        if self.config.include_alembic:
            steps.append("Run 'make migration msg=\"initial\"' to create first migration")
            steps.append("Run 'make migrate' to apply migrations")

        if self.config.project_type == "work":
            steps.append("Link repo(s) to Azure App Service / Static Web Apps in the Azure portal")
        else:
            steps.append("Connect repo to Render.com and use the render.yaml blueprint")

        return steps

    def validate(self) -> dict:
        """Validate that all expected files exist in the project."""
        missing = []
        expected = self._expected_files()
        for f in expected:
            if not (self.project_root / f).exists():
                missing.append(f)

        return {
            "status": "valid" if not missing else "invalid",
            "project_root": str(self.project_root),
            "total_expected": len(expected),
            "missing_files": missing,
            "missing_count": len(missing),
        }

    def _expected_files(self) -> list[str]:
        """List files expected in a scaffolded project."""
        files = [
            SCAFFOLD_METADATA_FILE,
            "README.md",
            "CLAUDE.md",
            ".env.example",
            "Makefile",
            "docker-compose.yml",
            "docker-compose.override.yml",
        ]

        if self.config.is_multi_repo:
            api_prefix = f"{self.config.name}-api"
            fe_prefix = f"{self.config.name}-frontend"
        else:
            api_prefix = ""
            fe_prefix = ""

        def api(p: str) -> str:
            return f"{api_prefix}/{p}" if api_prefix else p

        files.extend(
            [
                api(".gitignore"),
                api("Dockerfile"),
                api("pyproject.toml"),
                api("startup.sh"),
                api("app/__init__.py"),
                api("app/main.py"),
                api("app/config.py"),
                api("app/database.py"),
                api("app/dependencies.py"),
                api("app/models/__init__.py"),
                api("app/models/base.py"),
                api("app/models/user.py"),
                api("app/schemas/__init__.py"),
                api("app/schemas/common.py"),
                api("app/schemas/user.py"),
                api("app/routers/__init__.py"),
                api("app/routers/health.py"),
                api("app/routers/users.py"),
                api("tests/__init__.py"),
                api("tests/conftest.py"),
                api("tests/test_health.py"),
            ]
        )

        if self.config.include_alembic:
            files.extend(
                [
                    api("alembic.ini"),
                    api("alembic/env.py"),
                    api("alembic/script.py.mako"),
                    api("alembic/versions/.gitkeep"),
                ]
            )

        if self.config.include_sse:
            files.append(api("app/routers/sse.py"))

        if self.config.include_auth:
            files.extend(
                [
                    api("app/auth/__init__.py"),
                    api("app/auth/jwt.py"),
                    api("app/auth/routes.py"),
                ]
            )

        if self.config.frontend_type == "react":

            def fe(p: str) -> str:
                return f"{fe_prefix}/{p}" if fe_prefix else p

            files.extend(
                [
                    fe(".gitignore"),
                    fe("Dockerfile"),
                    fe("package.json"),
                    fe("vite.config.ts"),
                    fe("tsconfig.json"),
                    fe("index.html"),
                    fe("src/main.tsx"),
                    fe("src/App.tsx"),
                ]
            )
        else:
            files.extend(
                [
                    api("app/templates/base.html"),
                    api("app/templates/index.html"),
                    api("app/routers/pages.py"),
                ]
            )

        if self.config.project_type == "work":
            files.append(api(".github/workflows/ci.yml"))
            if self.config.frontend_type == "react":
                fe_prefix_val = fe_prefix or ""

                def fe2(p: str) -> str:
                    return f"{fe_prefix_val}/{p}" if fe_prefix_val else p

                files.append(fe2(".github/workflows/ci.yml"))
                files.append(fe2(".github/workflows/deploy.yml"))
        else:
            files.append("render.yaml")

        return files

    def info(self) -> dict:
        """Return information about the scaffolded project."""
        meta_path = self.project_root / SCAFFOLD_METADATA_FILE
        meta = json.loads(meta_path.read_text())
        return {
            "project_root": str(self.project_root),
            "config": meta,
            "structure": "multi-repo" if self.config.is_multi_repo else "single-repo",
        }

    def add_component(self, component_config: ComponentConfig) -> dict:
        """Add a component to an existing project."""
        from project_scaffold.renderers.api import add_router, add_model

        if component_config.component == "api_router":
            return add_router(self, component_config)
        elif component_config.component == "db_model":
            return add_model(self, component_config)
        else:
            return {
                "status": "error",
                "message": f"Component type '{component_config.component}' not yet implemented",
            }
