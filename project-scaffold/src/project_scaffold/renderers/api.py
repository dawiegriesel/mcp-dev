from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from project_scaffold.config import PYDANTIC_TYPES_MAP, SCAFFOLD_METADATA_FILE, SQLALCHEMY_TYPES_MAP

if TYPE_CHECKING:
    from project_scaffold.generator import ProjectGenerator
    from project_scaffold.models import ComponentConfig


def add_router(generator: "ProjectGenerator", config: "ComponentConfig") -> dict:
    """Add a new API router + schema to an existing project."""
    api_root = generator._api_root()
    name = config.name.lower()
    fields = config.fields or {}

    # Generate the SQLAlchemy model if fields are provided
    if fields:
        result = add_model(generator, config)
        if result["status"] == "error":
            return result

    # Generate the router
    router_path = api_root / "app" / "routers" / f"{name}.py"
    if router_path.exists():
        return {"status": "error", "message": f"Router already exists: {router_path}"}

    router_content = _generate_router(name, fields, generator.config.include_auth)
    generator._write(router_path, router_content)

    # Generate the schema if not already done via add_model
    if not fields:
        schema_path = api_root / "app" / "schemas" / f"{name}.py"
        if not schema_path.exists():
            schema_content = _generate_schema(name, fields)
            generator._write(schema_path, schema_content)

    # Update .scaffold.json
    _update_metadata(generator.project_root, "api_router", name)

    return {
        "status": "success",
        "component": "api_router",
        "name": name,
        "files_created": generator.files_created,
        "next_steps": [
            f"Add `from app.routers import {name}` to app/main.py",
            f'Add `app.include_router({name}.router, prefix="/api/{name}", tags=["{name}"])` to app/main.py',
        ],
    }


def add_model(generator: "ProjectGenerator", config: "ComponentConfig") -> dict:
    """Add a new SQLAlchemy model + Pydantic schema to an existing project."""
    api_root = generator._api_root()
    name = config.name.lower()
    fields = config.fields or {}

    # Generate model
    model_path = api_root / "app" / "models" / f"{name}.py"
    if model_path.exists():
        return {"status": "error", "message": f"Model already exists: {model_path}"}

    model_content = _generate_model(name, fields)
    generator._write(model_path, model_content)

    # Generate schema
    schema_path = api_root / "app" / "schemas" / f"{name}.py"
    if not schema_path.exists():
        schema_content = _generate_schema(name, fields)
        generator._write(schema_path, schema_content)

    # Update .scaffold.json
    _update_metadata(generator.project_root, "db_model", name)

    return {
        "status": "success",
        "component": "db_model",
        "name": name,
        "files_created": generator.files_created,
        "next_steps": [
            f"Import the model in alembic/env.py: `from app.models import {name}`",
            f"Run 'make migration msg=\"add {name}\"' to create migration",
            "Run 'make migrate' to apply",
        ],
    }


def _generate_model(name: str, fields: dict[str, str]) -> str:
    """Generate a SQLAlchemy model file."""
    class_name = name.capitalize()
    lines = [
        "from sqlalchemy import String",
        "from sqlalchemy.orm import Mapped, mapped_column",
        "",
        "from app.models.base import Base, TimestampMixin",
        "",
        "",
        f"class {class_name}(TimestampMixin, Base):",
        f'    __tablename__ = "{name}s"',
        "",
        "    id: Mapped[int] = mapped_column(primary_key=True)",
    ]

    sa_imports = set()
    for field_name, field_type in fields.items():
        sa_type = SQLALCHEMY_TYPES_MAP.get(field_type.lower(), "String")
        sa_imports.add(sa_type)
        if sa_type == "String":
            lines.append(f"    {field_name}: Mapped[str] = mapped_column(String(255))")
        else:
            py_type = PYDANTIC_TYPES_MAP.get(field_type.lower(), "str")
            lines.append(f"    {field_name}: Mapped[{py_type}] = mapped_column()")

    # Fix imports
    all_sa_types = {"String"} | sa_imports
    import_line = f"from sqlalchemy import {', '.join(sorted(all_sa_types))}"
    lines[0] = import_line

    return "\n".join(lines) + "\n"


def _generate_schema(name: str, fields: dict[str, str]) -> str:
    """Generate Pydantic v2 schema file."""
    class_name = name.capitalize()
    lines = [
        "from datetime import datetime",
        "",
        "from pydantic import BaseModel, ConfigDict",
        "",
        "",
        f"class {class_name}Base(BaseModel):",
    ]

    if fields:
        for field_name, field_type in fields.items():
            py_type = PYDANTIC_TYPES_MAP.get(field_type.lower(), "str")
            lines.append(f"    {field_name}: {py_type}")
    else:
        lines.append("    pass")

    lines.extend(
        [
            "",
            "",
            f"class {class_name}Create({class_name}Base):",
            "    pass",
            "",
            "",
            f"class {class_name}Update(BaseModel):",
        ]
    )

    if fields:
        for field_name, field_type in fields.items():
            py_type = PYDANTIC_TYPES_MAP.get(field_type.lower(), "str")
            lines.append(f"    {field_name}: {py_type} | None = None")
    else:
        lines.append("    pass")

    lines.extend(
        [
            "",
            "",
            f"class {class_name}Read({class_name}Base):",
            "    model_config = ConfigDict(from_attributes=True)",
            "",
            "    id: int",
            "    created_at: datetime",
            "    updated_at: datetime",
        ]
    )

    return "\n".join(lines) + "\n"


def _generate_router(name: str, fields: dict[str, str], include_auth: bool) -> str:
    """Generate a FastAPI router file."""
    class_name = name.capitalize()
    lines = [
        "from fastapi import APIRouter, Depends, HTTPException",
        "from sqlalchemy import select",
        "from sqlalchemy.ext.asyncio import AsyncSession",
        "",
        "from app.dependencies import get_db",
        f"from app.models.{name} import {class_name}",
        f"from app.schemas.{name} import {class_name}Create, {class_name}Read, {class_name}Update",
        "",
        "router = APIRouter()",
        "",
        "",
        f'@router.get("/", response_model=list[{class_name}Read])',
        f"async def list_{name}s(",
        "    skip: int = 0,",
        "    limit: int = 100,",
        "    db: AsyncSession = Depends(get_db),",
        "):",
        f"    result = await db.execute(select({class_name}).offset(skip).limit(limit))",
        "    return result.scalars().all()",
        "",
        "",
        f'@router.get("/{{{{item_id}}}}", response_model={class_name}Read)',
        f"async def get_{name}(item_id: int, db: AsyncSession = Depends(get_db)):",
        f"    result = await db.execute(select({class_name}).where({class_name}.id == item_id))",
        "    item = result.scalar_one_or_none()",
        "    if not item:",
        f'        raise HTTPException(status_code=404, detail="{class_name} not found")',
        "    return item",
        "",
        "",
        f'@router.post("/", response_model={class_name}Read, status_code=201)',
        f"async def create_{name}({name}_in: {class_name}Create, db: AsyncSession = Depends(get_db)):",
        f"    item = {class_name}(**{name}_in.model_dump())",
        "    db.add(item)",
        "    await db.commit()",
        "    await db.refresh(item)",
        "    return item",
        "",
        "",
        f'@router.patch("/{{{{item_id}}}}", response_model={class_name}Read)',
        f"async def update_{name}(",
        "    item_id: int,",
        f"    {name}_in: {class_name}Update,",
        "    db: AsyncSession = Depends(get_db),",
        "):",
        f"    result = await db.execute(select({class_name}).where({class_name}.id == item_id))",
        "    item = result.scalar_one_or_none()",
        "    if not item:",
        f'        raise HTTPException(status_code=404, detail="{class_name} not found")',
        "",
        f"    for field, value in {name}_in.model_dump(exclude_unset=True).items():",
        "        setattr(item, field, value)",
        "",
        "    await db.commit()",
        "    await db.refresh(item)",
        "    return item",
        "",
        "",
        f'@router.delete("/{{{{item_id}}}}", status_code=204)',
        f"async def delete_{name}(item_id: int, db: AsyncSession = Depends(get_db)):",
        f"    result = await db.execute(select({class_name}).where({class_name}.id == item_id))",
        "    item = result.scalar_one_or_none()",
        "    if not item:",
        f'        raise HTTPException(status_code=404, detail="{class_name} not found")',
        "",
        "    await db.delete(item)",
        "    await db.commit()",
    ]

    return "\n".join(lines) + "\n"


def _update_metadata(project_root: Path, component_type: str, name: str) -> None:
    """Update .scaffold.json with the new component."""
    meta_path = project_root / SCAFFOLD_METADATA_FILE
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta.setdefault("components", []).append(
            {
                "type": component_type,
                "name": name,
            }
        )
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
