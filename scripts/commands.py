#!/usr/bin/env python
# mypy: ignore-errors
"""Command runner for the autheon project.

This script centralizes all development and CI commands in one place.
"""
import argparse
import os
import subprocess
import sys
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[str] = None) -> int:
    """Run a command and stream output in real-time."""
    print(f"Running: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd
    )

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())

    return process.poll()


def setup_venv() -> None:
    """Set up the virtual environment."""
    run_command(["uv", "venv"])
    run_command(["uv", "pip", "install", "--upgrade", "pip"])
    run_command(["uv", "pip", "install", "-e", "."])
    print("\033[32mDevelopment environment ready!\033[0m")


def lint() -> int:
    """Run mypy type checking."""
    return run_command(["uv", "run", "mypy", "."])


def format_code() -> int:
    """Format code with ruff."""
    status1 = run_command(["uv", "run", "ruff", "--exit-non-zero-on-fix", "--fix-only"])
    status2 = run_command(["uv", "run", "ruff", "format"])
    status3 = run_command(["uv", "run", "ruff", "format", "--check"])
    return max(status1, status2, status3)


def test() -> int:
    """Run tests with pytest."""
    return run_command(["uv", "run", "pytest"])


def coverage() -> int:
    """Run test coverage."""
    status1 = run_command(["uv", "run", "coverage", "run"])
    status2 = run_command(["uv", "run", "coverage", "combine"])
    status3 = run_command(["uv", "run", "coverage", "report"])
    status4 = run_command(["uv", "run", "coverage", "html"])
    return max(status1, status2, status3, status4)


def clean() -> None:
    """Clean build artifacts."""
    run_command(["uv", "run", "coverage", "erase"])
    dirs_to_remove = [
        "app.egg-info",
        "build",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        "site",
    ]
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            subprocess.run(["rm", "-rf", dir_path])
    print("\033[32mCleaned!\033[0m")


def install_hooks() -> None:
    """Install git hooks."""
    run_command(["uv", "run", "pre-commit", "install"])
    run_command(["./scripts/pre-push"])


def serve_app() -> int:
    """Serve the app locally."""
    run_command(["uv", "pip", "install", "uvicorn"])
    return run_command(
        ["uv", "run", "uvicorn", "app.app:app", "--reload", "--port=6969"]
    )


def serve_docs() -> int:
    """Serve documentation locally."""
    run_command(["uv", "pip", "install", "mkdocs", "mkdocs-material", "mkdocstrings"])
    return run_command(["uv", "run", "mkdocs", "serve"])


def build_docs() -> int:
    """Build documentation."""
    run_command(
        [
            "uv",
            "pip",
            "install",
            "mkdocs>=1.5.3,<2.0.0",
            "mkdocs-material>=9.1.21,<10.0.0",
            "mkdocstrings[python]>=0.24.0,<0.25.0",
            "mkdocs-material-extensions>=1.3.1,<2.0.0",
        ]
    )
    return run_command(["uv", "run", "mkdocs", "build"])


def lock_dependencies() -> int:
    """Lock dependencies."""
    return run_command(
        ["uv", "pip", "compile", "pyproject.toml", "-o", "requirements.lock"]
    )


def sync_dependencies() -> int:
    """Sync dependencies from lock file."""
    return run_command(["uv", "pip", "sync", "requirements.lock"])


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Autheon development command runner")
    parser.add_argument(
        "command",
        choices=[
            "setup",
            "lint",
            "format",
            "test",
            "coverage",
            "clean",
            "hooks",
            "serve-app",
            "serve-docs",
            "build-docs",
            "lock",
            "sync",
            "info",
        ],
        help="Command to run",
    )

    args = parser.parse_args()

    commands = {
        "setup": setup_venv,
        "lint": lint,
        "format": format_code,
        "test": test,
        "coverage": coverage,
        "clean": clean,
        "hooks": install_hooks,
        "serve-app": serve_app,
        "serve-docs": serve_docs,
        "build-docs": build_docs,
        "lock": lock_dependencies,
        "sync": sync_dependencies,
        "info": lambda: print(f"Running on {os.uname().machine} machine"),
    }

    exit_code = commands[args.command]()
    sys.exit(exit_code if isinstance(exit_code, int) else 0)


if __name__ == "__main__":
    main()
