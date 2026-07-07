#!/usr/bin/env bash

set -e

echo "==> Syncing dependencies"
uv sync --all-groups

echo "==> Installing pre-commit hooks"
uv run pre-commit install

echo "==> Running checks"
make check

echo
echo "Project is ready."
