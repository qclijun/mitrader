# Repository Guidelines

## Project Structure & Module Organization

`app.py` is the Streamlit entry point for the trading analysis UI. Core logic lives in `src/`: `data_loader.py` handles trade and price data loading, `chart_builder.py` builds Plotly K-line charts and markers, and `utils.py` contains shared helpers. Tests are organized under `tests/unit`, `tests/integration`, and `tests/e2e`, with common fixtures in `tests/fixtures` and `tests/conftest.py`. Example input files live in `sample_data/`. Planning and design notes are kept under `docs/superpowers/`. `graphify-out/` contains generated codebase graph artifacts.

## Build, Test, and Development Commands

- `uv sync`: install project and development dependencies from `uv.lock`.
- `uv run streamlit run app.py`: start the local app, normally at `http://localhost:8501`.
- `uv run pytest`: run the full pytest suite with settings from `pytest.ini`.
- `uv run pytest tests/unit`: run only unit tests.
- `uv run pytest -m integration`: run tests marked as integration.
- `uv run pytest -m e2e`: run Playwright-backed end-to-end tests.

## Coding Style & Naming Conventions

Use Python 3.14 or newer. Follow the existing style: 4-space indentation, descriptive snake_case functions and variables, and small modules grouped by responsibility. Prefer Polars APIs for dataframe work and Plotly APIs for chart construction. Keep Streamlit UI orchestration in `app.py`; put reusable loading, transformation, and chart logic in `src/`. Test files should be named `test_*.py`, classes `Test*`, and test functions `test_*`.

## Testing Guidelines

Pytest is the test runner. `pytest.ini` defines test discovery and the `unit`, `integration`, and `e2e` markers. Add focused unit tests for pure helpers and data transformations, integration tests for multi-module data flows, and e2e tests for user-visible Streamlit behavior. When changing chart output, assert on stable figure structure, traces, marker text, and data ranges rather than visual snapshots alone.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style prefixes such as `feat:`, `fix:`, and `refactor:`. Keep commits focused and imperative, for example `fix: strip whitespace from bond names`. Pull requests should describe the user-facing change, mention affected data formats or sample files, link related issues when available, and include screenshots or short recordings for UI changes. Note the test command run before review.

## Agent-Specific Instructions

Before answering architecture or codebase questions, inspect `graphify-out/GRAPH_REPORT.md` when present. After modifying code files, run `graphify update .` to refresh the generated graph. Do not commit generated `graphify-out/cache` churn unless the task explicitly includes graph maintenance.
