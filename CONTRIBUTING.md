# Contributing to Knowai

Thank you for considering contributing! Knowai is open source under MIT.

## Quick start

```bash
git clone https://github.com/qorstack/knowai
cd knowai
uv sync                  # install deps
uv run pytest            # run tests
uv run ruff check src/   # lint
```

## How to contribute

### Reporting bugs

Open a [GitHub issue](https://github.com/qorstack/knowai/issues) with:

- What you ran (CLI command, MCP tool call, etc.)
- What you expected
- What happened
- Python version + OS
- Output of `knowai scan .` if relevant

### Proposing features

Open a [GitHub Discussion](https://github.com/qorstack/knowai/discussions) first to align on direction. Knowai has a clear thesis (cognitive enforcement before code generation) — features that don't fit will be politely declined.

### Submitting PRs

1. Fork + branch from `main`
2. Write tests for new behavior
3. Run `uv run pytest` (everything green)
4. Run `uv run ruff check src/ && uv run ruff format src/`
5. Open PR with clear description

## Architecture

Knowai has 6 layers under `src/knowai/`:

| Layer | Package |
|---|---|
| Scanner | `scanner/` |
| Cognitive Graph | `graph/` |
| Memory | `memory/` |
| Cognition Packs | `packs/` |
| Reasoning | `reasoning/` |
| MCP Server | `mcp/` |

Plus surfaces: `cli/`, `api/`, `workspace/`, `approval/`, `link/`.

See [docs/architecture.md](docs/architecture.md) for details.

## Coding guidelines

- **Simplicity first** — minimum code that solves the problem
- **No LLM calls in the reasoning engine** — rule-based, deterministic
- **MCP-first** — every cognition feature should be reachable via MCP tools, not just CLI
- **Backward compatible** — additive changes preferred; deprecate before removing
- **Test what matters** — integration tests > unit tests for cognition logic

## Adding a Cognition Pack

Built-in packs live in [src/knowai/packs/builtin.py](src/knowai/packs/builtin.py). Each pack has:

```python
CognitionPack(
    domain="search",
    description="Full-text search domain",
    business_rules=["..."],
    common_requirements=["..."],
    risk_flags=["..."],
    required_workflow=["..."],
    forbidden_shortcuts=["..."],
    questions_to_ask=["..."],
)
```

Open a PR with the pack + a test in [tests/test_packs.py](tests/test_packs.py).

## Releasing

Maintainers only:

```bash
# Bump version in pyproject.toml + src/knowai/__init__.py
git tag v0.X.0
git push --tags
# GitHub Actions publishes to PyPI
```

## Internal design docs

For deep-dive specs and roadmap, see [`internal/`](internal/) — these are not user-facing but document design decisions.

## License

By contributing, you agree your contributions will be licensed under MIT.
