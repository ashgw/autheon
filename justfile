alias i := install
alias l := lint
alias c := coverage
alias cn := clean
alias t := test
alias f := format
alias h := hooks
alias d := serve-docs
alias b := build-docs

@help:
    just --list

@install:
    uv venv
    source .venv/bin/activate
    uv pip install --upgrade pip
    uv pip install -e .
    echo -e "\e[32mDevelopment environment ready!\e[0m"

@lint:
    uv run mypy .


@format:
    uv run ruff --exit-non-zero-on-fix --fix-only
    uv run ruff format
    uv run ruff format --check

@test:
    uv run pytest

@coverage:
    uv run coverage run
    uv run coverage combine
    uv run coverage report
    uv run coverage html

@clean:
    coverage erase
    rm -rf app.egg-info build .ruff_cache .pytest_cache .mypy_cache site
    echo -e "\e[32mCleaned!\e[0m"

@hooks:
    uv run pre-commit install
    ./scripts/pre-push

@serve-app:
    uv pip install uvicorn
    uv run uvicorn app.app:app --reload --port=6969

@serve-docs:
    uv pip install mkdocs mkdocs-material mkdocstrings
    uv run mkdocs serve

@build-docs:
    uv pip install mkdocs mkdocs-material mkdocstrings
    uv run mkdocs build

@info:
    echo "Running on {{arch()}} machine"

@lock:
    uv pip compile pyproject.toml -o requirements.lock

@sync:
    uv pip sync requirements.lock
