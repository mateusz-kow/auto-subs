# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
