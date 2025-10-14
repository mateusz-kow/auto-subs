# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2024-05-28

### Added
-   **Expanded Test Suite**: Added comprehensive tests for the programmatic editing API, including edge cases for resizing, splitting, and merging subtitle segments.
-   **CLI Robustness Tests**: Added tests to verify CLI argument parsing for advanced ASS styling and to ensure correct error handling in batch processing jobs.

### Changed
-   **Refactored CLI Internals**: Consolidated the logic for parsing ASS style settings from command-line arguments into a shared utility function, reducing code duplication between the `generate` and `transcribe` commands.
-   **Updated Documentation**: Significantly improved `README.md`, `ROADMAP.md`, and `CONTRIBUTING.md` to better reflect the project's current capabilities, fix inconsistencies, and clarify usage examples.

## [0.4.0] - 2024-05-27

### Added

-   **Multi-line Segment Generation**: Introduced a `--max-lines` option to the CLI and API to group individual lines into professional, multi-line subtitle segments with correctly adjusted timings.
-   **Advanced ASS Styling**: The `generate` and `transcribe` commands now accept a `--style-file` argument to load style settings from a JSON file, along with numerous granular flags for overriding specific styles (e.g., `--font-name`, `--primary-color`).
-   **Enhanced Data Validation**: The `Subtitles` model now automatically detects and logs a warning for segments with overlapping timestamps, improving the quality and reliability of parsed files.
-   **Serializable JSON Format**: Added a dedicated `json` output format that converts subtitle models back into a Whisper-compatible JSON structure, allowing for lossless data round-trips.
-   **Public Core Utilities**: Exposed core timestamp formatting and parsing functions (e.g., `format_srt_timestamp`, `srt_timestamp_to_seconds`) in the main package namespace, making them available for developers.

### Changed

-   The public API functions `generate()` and `transcribe()` can now accept a `pathlib.Path` or `str` for transcription sources, providing more flexible inputs for developers.
-   The CLI now infers the desired output format from the output file's extension (e.g., `-o video.vtt`) if the `--format` flag is not explicitly provided.

## [0.3.3] - 2024-05-24

### Changed

-   Greatly improved and expanded the `README.md` with examples for all major features, including transcription, generation, and conversion.
-   Refined the CLI output for better clarity and a more consistent user experience across all commands.

### Fixed

-   Ensured the `PathProcessor` for batch operations provides clearer feedback when an input directory contains no supported files.

## [0.3.2] - 2024-05-23

### Added

-   **Subtitle Conversion Engine**: Implemented parsers for SRT, VTT, and ASS formats, allowing the library to read and understand existing subtitle files.
-   **New `convert` CLI Command**: Added `auto-subs convert` to easily convert between supported subtitle formats (e.g., SRT to VTT) from the command line. This command also supports batch processing directories.
-   **New `load()` API Function**: Exposed `auto_subs.load()` to allow developers to programmatically load subtitle files into an `auto_subs.Subtitles` object for inspection or further processing.

## [0.3.1] - 2024-05-22

### Changed

-   Polished documentation and updated type hints for clarity.
-   Minor improvements to the CI workflow configuration.

## [0.3.0] - 2024-05-22

### Added

-   **Direct Audio/Video Transcription**: Added a new `transcribe` command to the CLI and an `auto_subs.transcribe()` function to the API. This allows for end-to-end subtitle generation directly from media files by integrating `openai-whisper`.
-   **Whisper Model Selection**: Users can now choose the Whisper model size (e.g., `tiny`, `base`, `small`) via the `--model` flag in the CLI or the `model_name` parameter in the API.
-   **Batch Processing**: Both the `generate` and `transcribe` CLI commands now support processing entire directories of files at once.
-   A new `[transcribe]` optional dependency was added to keep the core library lightweight for users who only need to generate subtitles from existing JSON files.

## [0.2.0] - 2024-05-21

### Added

-   **VTT Subtitle Support**: Added support for generating WebVTT (`.vtt`) subtitle files, a common format for web videos.
-   **Karaoke-Style ASS Highlighting**: Implemented karaoke-style (`{\k...}`) word-by-word timing for ASS subtitles. This can be enabled via `AssSettings` in the library or the `--karaoke` flag in the CLI.
-   `CHANGELOG.md` to track project changes.
-   `CONTRIBUTING.md` to provide guidelines for new contributors.

### Changed

-   Updated `ruff format` to `ruff format --check` in the CI workflow to enforce formatting without modifying files.

## [0.1.0] - 2024-05-20

-   Initial public release of `auto-subs`.
