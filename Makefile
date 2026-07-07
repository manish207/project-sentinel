.PHONY: test lint fmt typecheck check run clean

run:
	uv run project-sentinel

test:
	uv run pytest -v

lint:
	uv run ruff check .

fmt:
	uv run black .

typecheck:
	uv run mypy src tests

check:
	uv run ruff check .
	uv run black --check .
	uv run mypy src tests
	uv run pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
