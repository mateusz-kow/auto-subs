# Contributing to Auto-Subs

First off, thank you for considering contributing to `auto-subs`! Your help is greatly appreciated.

## Getting Started

### Setting up the Development Environment

1.  **Fork and Clone the Repository**:
    Fork the repository on GitHub and then clone it to your local machine.

    ```bash
    git clone https://github.com/mateusz-kow/auto-subs.git
    cd auto-subs
    ```

2.  **Install Dependencies**:
    This project uses `uv` for fast dependency management. We recommend creating a virtual environment.

    ```bash
    # Create a virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`

    # Install the project in editable mode with development dependencies
    uv pip install -e .[dev]
    ```

### Running Checks and Tests

Before submitting your changes, please ensure that all checks and tests pass.

1.  **Linting with Ruff**:
    Ruff is used for linting. To check for linting errors and apply automatic fixes:

    ```bash
    uv run ruff check . --fix
    ```

2.  **Formatting with Ruff**:
    To check the codebase according to the project's style:

    ```bash
    uv run ruff format --check .
    ```

3.  **Type Checking with Mypy**:
    This project uses strict type checking with Mypy. To run the type checker:

    ```bash
    uv run mypy
    ```

4.  **Running Tests with Pytest**:
    To run the full test suite and generate a coverage report:

    ```bash
    uv run pytest --cov=auto_subs
    ```

## Submitting a Pull Request

1.  Create a new branch for your feature or bug fix: `git checkout -b feature/my-new-feature` or `bugfix/issue-description`.
2.  Make your changes and commit them with a clear, descriptive message.
3.  Push your branch to your fork: `git push origin feature/my-new-feature`.
4.  Open a pull request from your fork to the `main` branch of the original repository.
5.  In the pull request description, please explain the changes you made and reference any related issues.

Thank you for your contribution!
