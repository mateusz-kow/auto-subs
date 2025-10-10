# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
