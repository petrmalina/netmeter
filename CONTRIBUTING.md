# Contributing to NetMeter

Thank you for considering contributing to NetMeter! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/petrmalina/netmeter.git
cd netmeter
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Code Standards

- **Python 3.10+** — use type hints where practical
- **Formatting** — enforced by [Ruff](https://docs.astral.sh/ruff/) (`ruff format`)
- **Linting** — enforced by Ruff (`ruff check`)
- **Type checking** — Mypy (`mypy src/`)
- **Tests** — pytest with ≥80% coverage

All checks run automatically in CI on every pull request.

## Running Checks Locally

```bash
ruff check src/ tests/        # lint
ruff format src/ tests/        # format
mypy src/netmeter/             # type check
pytest --cov=netmeter          # tests with coverage
```

## Pull Request Process

1. Fork the repository and create a feature branch from `main`
2. Make your changes with tests
3. Ensure all checks pass locally
4. Open a pull request against `main`
5. Wait for CI to pass and a review

## Commit Messages

Use conventional commit style:
- `feat: add X` — new features
- `fix: resolve Y` — bug fixes
- `docs: update Z` — documentation
- `test: add tests for W` — tests
- `ci: update pipeline` — CI changes
- `deps: bump X` — dependency updates

## Project Structure

```
src/netmeter/
├── __init__.py      # package version
├── config.py        # 12-factor configuration from env vars
├── cli.py           # CLI entry points
├── database.py      # SQLite data access
├── dashboard.py     # HTML + graph generation
├── measure.py       # speed test execution
├── network.py       # network detection
└── scheduler.py     # built-in periodic scheduler
tests/
├── test_config.py
├── test_database.py
├── test_dashboard.py
├── test_measure.py
└── test_network.py
```

## Reporting Issues

Use [GitHub Issues](https://github.com/petrmalina/netmeter/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- OS, Python version, and Docker version (if applicable)
