import nox
from nox.sessions import Session

# Default sessions to run when no sessions are specified
nox.options.sessions = ["lint", "typecheck", "tests"]

# Python versions to test against
PYTHON_VERSIONS = ["3.11", "3.12"]


@nox.session(python=PYTHON_VERSIONS[0])
def lint(session: Session) -> None:
    """Run the linter (ruff)."""
    session.install("ruff")
    session.run("ruff", "check", ".")


@nox.session(python=PYTHON_VERSIONS[0])
def format(session: Session) -> None:
    """Run the formatter (ruff format)."""
    session.install("ruff")
    # The --check flag is used in CI to fail if any files need reformatting.
    # To reformat files locally, run `nox -s format -- --no-check`.
    session.run("ruff", "format", ".", *session.posargs)


@nox.session(python=PYTHON_VERSIONS)
def typecheck(session: Session) -> None:
    """Run the type checker (pyright)."""
    # Install the project itself with dev dependencies in editable mode
    session.install("-e", ".[dev]")
    session.run("pyright")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite (pytest) and generate a coverage report."""
    session.install("-e", ".[dev]")
    session.run(
        "pytest",
        "--cov=auto_subs",
        "--cov-report=xml:coverage.xml",  # Generate XML report for CI
        "--cov-report=term",  # Show a summary in the terminal
        *session.posargs,
    )
