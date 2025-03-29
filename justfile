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
    uv run python scripts/commands.py setup

@lint:
    uv run python scripts/commands.py lint

@format:
    uv run python scripts/commands.py format

@test:
    uv run python scripts/commands.py test

@coverage:
    uv run python scripts/commands.py coverage

@clean:
    uv run python scripts/commands.py clean

@hooks:
    uv run python scripts/commands.py hooks

@serve-app:
    uv run python scripts/commands.py serve-app

@serve-docs:
    uv run python scripts/commands.py serve-docs

@build-docs:
    uv run python scripts/commands.py build-docs

@info:
    uv run python scripts/commands.py info

@lock:
    uv run python scripts/commands.py lock

@sync:
    uv run python scripts/commands.py sync
