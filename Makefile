.PHONY: lint format test

lint:
	uv run ruff check .
	uv run black --check .

format:
	uv run black .
	uv run ruff check --fix .

test:
	uv run pytest
