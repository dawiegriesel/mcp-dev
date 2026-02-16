# Contributing

Contributions are welcome! This project is under active development and we appreciate help from the community.

## Before you start

- Read the [Code of Conduct](CODE_OF_CONDUCT.md) — all contributors are expected to follow it
- Check [open issues](https://github.com/dawiegriesel/mcp-dev/issues) to see if your idea or bug is already tracked
- For larger changes, open an issue first to discuss your approach before writing code

## Getting started

1. Fork the repo and clone your fork
2. Install dependencies:
   ```bash
   uv sync --extra dev
   ```
3. Create a branch for your change:
   ```bash
   git checkout -b my-feature
   ```

## Development workflow

```bash
# Run the MCP server locally
uv run project-scaffold

# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Run tests
uv run pytest
```

## Submitting changes

1. Keep pull requests focused — one feature or fix per PR
2. Follow existing code style (Ruff handles formatting, 100-char line length)
3. Add tests for new functionality where applicable
4. Update documentation (README, CHANGELOG) if your change affects user-facing behavior
5. Open a pull request against `main` with a clear description of what and why

## Reporting bugs

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Python version and OS

## Feature requests

Open an issue describing the use case and proposed solution. Discussion before implementation helps avoid duplicate effort.
