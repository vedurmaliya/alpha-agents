# Contributing to AlphaAgents

Thank you for your interest in contributing to **AlphaAgents**. This project is intended to be collaborative, transparent, and welcoming to contributors of all levels. The guidelines below are designed to make contributions efficient, maintain high code quality, and ensure reproducibility of experiments.

---

## Table of contents

1. [How to contribute](#how-to-contribute)
2. [Reporting issues & requesting features](#reporting-issues--requesting-features)
3. [Development setup](#development-setup)
4. [Branching & commit conventions](#branching--commit-conventions)
5. [Code style & quality](#code-style--quality)
6. [Testing & CI](#testing--ci)
7. [Pull request process](#pull-request-process)
8. [Documentation](#documentation)
9. [Security reporting](#security-reporting)
10. [Maintainers & governance](#maintainers--governance)
11. [License](#license)

---

## How to contribute

Contributions are welcome in many forms: bug fixes, new features, documentation improvements, tests, examples, and reproducibility artifacts. The preferred workflow is:

1. Fork the repository.
2. Create a feature branch from `main` (see branch naming below).
3. Implement your changes and include tests where applicable.
4. Run the test suite and linters locally.
5. Open a pull request to `main` with a clear description and rationale.

If your change is substantial, open an issue first to discuss design and scope.

---

## Reporting issues & requesting features

* Use GitHub Issues for bug reports and feature requests.
* A good bug report includes: environment (OS, Python version), steps to reproduce, expected vs actual behavior, and minimal code/data to reproduce.
* For feature requests, explain the user story, motivation, and a proposed approach or API sketch.

---

## Development setup

These steps will get a local copy running for development and testing:

1. Fork and clone the repository.
2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and populate required API keys (GROQ\_API\_KEY, etc.).
4. Optionally, run a small PoC ingest and one agent run to verify the environment:

```bash
python scripts/ingest_prices.py --ticker AAPL
python orchestration/run_one_round.py --ticker AAPL
```

---

## Branching & commit conventions

Branch naming (examples):

* `feature/<short-description>` — for new features
* `fix/<short-description>` — for bug fixes
* `docs/<short-description>` — for docs updates

Commit messages should be clear and atomic. Use present tense and reference issues when applicable:

```
Add valuation agent for DCF calculations
Fix #123
```

Consider using conventional commits if you maintain automated changelog generation.

---

## Code style & quality

* Follow **PEP 8** for Python style. Use `black` for formatting and `ruff`/`flake8` for linting.
* Include type annotations and prefer small, testable functions.
* Keep business logic and orchestration code separated for easier testing.

Recommended developer tools:

* `black` (formatter)
* `ruff` or `flake8` (linting)
* `isort` (import ordering)

---

## Testing & CI

* Add pytest-based tests under the `tests/` directory.
* Aim for unit tests for small components (parsers, utilities) and integration tests for higher-level flows (ingestion, a single-agent run using mocked LLM responses).
* The repository includes a GitHub Actions workflow to run tests and linters on pull requests. Ensure your changes pass the pipeline before requesting review.

Guidelines for tests:

* Keep external dependencies mocked (Groq/LangGraph calls) to avoid API costs in CI.
* Use small synthetic datasets for fast unit/integration tests.

---

## Pull request process

When opening a PR:

* Target the `main` branch unless otherwise stated.
* Provide a clear title and description, list related issues, and include screenshots/outputs when relevant.
* Ensure tests pass and linting is satisfied.
* Keep PRs focused and avoid mixing unrelated changes.

Review expectations:

* Maintainers will review within a reasonable timeframe; requests for changes are normal.
* Be responsive to reviewer feedback and iterate on the PR.

---

## Documentation

* Keep README up-to-date with installation and usage examples.
* Add reproducible notebooks under `notebooks/` for experiments and plots.
* API-level docstrings should be present for public modules and classes.

---

## Security reporting

If you discover a security vulnerability, please do not open a public issue. Instead, contact the maintainers directly via the repository owner email or a private channel (see project profile). Provide steps to reproduce and an impact assessment.

---

## Maintainers & governance

The project maintainers are responsible for reviewing PRs, triaging issues, and releasing new versions. Substantial contributions may be invited to become maintainers. For formal governance or commercial use, contact the project owner.

---

## License

By contributing, you agree that your contributions will be licensed under the project license (MIT). See `LICENSE` for details.

---

Thank you for helping improve AlphaAgents — your contributions are highly appreciated.
