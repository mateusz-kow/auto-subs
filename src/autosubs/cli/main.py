import logging
from typing import Annotated

import typer

from autosubs import __version__
from autosubs.cli.burn import burn
from autosubs.cli.convert import convert
from autosubs.cli.generate import generate
from autosubs.cli.transcribe import transcribe

# The logger is configured in the main() callback based on CLI flags.
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="A powerful, local-first CLI for video transcription and subtitle generation.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)

app.command()(generate)
app.command()(convert)
app.command()(transcribe)
app.command()(burn)


def version_callback(value: bool) -> None:
    """Prints the version of the application and exits."""
    if value:
        typer.echo(f"auto-subs version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show the application's version and exit.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress all output except for errors."),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose logging. Use -vv for more detail.",
            count=True,
            is_eager=True,
        ),
    ] = 0,
) -> None:
    """Configure logging and manage the CLI application."""
    if quiet and verbose > 0:
        raise typer.BadParameter("--quiet and --verbose options cannot be used together.")

    log_level = logging.INFO
    if quiet:
        log_level = logging.WARNING
    elif verbose >= 1:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.debug(f"Verbose logging enabled. Level set to: {logging.getLevelName(log_level)}")


__all__ = ["app"]
