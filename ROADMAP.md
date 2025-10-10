# Auto-Subs Roadmap to 1.0.0

This document outlines the planned features and improvements for `auto-subs` as it progresses towards a stable `1.0.0` release. The goal of `1.0.0` is to provide a mature, feature-rich, and highly reliable tool for subtitle generation and conversion.

This roadmap is a living document and is subject to change based on development progress and community feedback.

## Current State: v0.2.0

-   **Core Functionality**: Generate subtitles from pre-existing Whisper JSON files.
-   **Supported Formats**: SRT, ASS, VTT, TXT.
-   **Features**: Intelligent word segmentation, karaoke-style highlighting for ASS, robust Pydantic-based data validation.
-   **Interfaces**: Python library API (`auto_subs.generate`) and a Typer-based CLI.

---

## Version 0.3.0 - Core Feature Expansion

This release will focus on making `auto-subs` a more self-contained tool by integrating transcription capabilities directly.

-   **🎯 Key Goal**: Move from a subtitle *formatter* to an end-to-end subtitle *generator*.
-   **Features**:
    -   **[Major] Direct Audio/Video Transcription**:
        -   Integrate the `openai-whisper` library to allow transcription directly from audio or video files.
        -   Add a new CLI command: `auto-subs transcribe <media_file>`.
        -   This command will handle audio extraction, transcription via Whisper, and then pass the result directly to the existing subtitle generation logic.
        -   The API will be expanded with a corresponding `auto_subs.transcribe()` function.
    -   **Batch Processing in CLI**:
        -   Allow the `generate` and `transcribe` commands to accept a directory as input to process multiple files at once.
        -   Example: `auto-subs transcribe ./episodes/ --format srt`.
    -   **Whisper Model Selection**:
        -   Allow users to select the Whisper model size (e.g., `tiny`, `base`, `small`, `medium`, `large`) via a CLI option (`--model`) and an API parameter.

---

## Version 0.4.0 - Universal Subtitle Conversion

This release introduces the ability to convert between existing subtitle formats, making `auto-subs` a versatile utility for any subtitle workflow.

-   **🎯 Key Goal**: Enable `auto-subs` to read, parse, and convert between existing subtitle formats.
-   **Features**:
    -   **[Major] Subtitle Parsing Engine**:
        -   Implement parsers for reading and understanding common subtitle formats.
        -   Initial support will be for SRT, VTT, and basic ASS (dialogue lines). This will involve parsing timestamps and text content into the internal `Subtitles` data model.
    -   **New CLI `convert` Command**:
        -   Add a new command: `auto-subs convert <input_file> -o <output_file>`.
        -   This allows for straightforward one-off conversions from the command line.
        -   Example: `auto-subs convert subtitles.ass -o subtitles.srt`.
    -   **New API Function `auto_subs.load()`**:
        -   Introduce a new public API function, `auto_subs.load()`, which takes a file path to a subtitle file and returns a `Subtitles` object.
        -   This enables developers to load, programmatically modify, and then re-export subtitles using the existing generator functions.

---

## Version 0.5.0 - Advanced Customization & Usability

This release will focus on giving users more fine-grained control over the subtitle output and improving the user experience.

-   **🎯 Key Goal**: Empower users with advanced styling and segmentation options.
-   **Features**:
    -   **Advanced ASS Styling via CLI**:
        -   Expose key `AssSettings` parameters as CLI options.
        -   Examples: `--ass-font "Comic Sans"`, `--ass-font-size 42`, `--ass-primary-color "&H0000FFFF&"`.
        -   This allows for extensive customization without writing Python code.
    -   **Enhanced Segmentation Logic**:
        -   Introduce a `--min-words-per-line` option to prevent single-word subtitle lines, which can be visually jarring.
        -   Add a `--max-lines` option (defaulting to 2) to control how many lines a single subtitle entry can have.
    -   **Output Format Inference**:
        -   Allow the CLI to automatically detect the desired output format from the file extension provided in the `--output` flag (e.g., `auto-subs generate in.json -o out.vtt` will automatically select VTT format).

---

## Version 0.6.0 - Robustness and Integration

This release will focus on hardening the tool against edge cases and making the API more flexible for developers.

-   **🎯 Key Goal**: Ensure maximum reliability and improve the developer experience.
-   **Features**:
    -   **Improved Data Validation and Correction**:
        -   Explicitly validate and, where possible, correct inverted timestamps (`start > end`) at the word level, logging a warning instead of failing.
        -   Add checks for overlapping word timestamps within a segment.
    -   **Flexible API Inputs**:
        -   Update `auto_subs.generate()` and `auto_subs.transcribe()` to optionally accept a file path (`str` or `Path`) in addition to a dictionary, simplifying common workflows.
    -   **Structured JSON Output**:
        -   Add a new output format: `json`. This format will output the cleaned, validated, and segmented subtitle data as a structured JSON file. This is useful for developers who want to use `auto-subs` as a pre-processing step in a larger toolchain.

---

## The Path to 1.0.0 (v0.7.0 - v0.9.x)

This phase will be dedicated to stabilization, documentation, and performance, with fewer new features.

-   **[v0.7.0] Comprehensive Documentation**:
    -   Set up a dedicated documentation website using MkDocs or Sphinx.
    -   Include a full API reference, tutorials for common use cases, and detailed explanations of all CLI commands and options.
-   **[v0.8.0] Performance Optimization**:
    -   Profile the application with very large transcription files (e.g., 2-3 hour videos).
    -   Optimize word segmentation, parsing, and file generation algorithms to reduce memory usage and processing time.
-   **[v0.9.0] Release Candidate Phase**:
    -   Focus exclusively on fixing bugs and incorporating feedback from early adopters.
    -   Freeze the API and feature set in preparation for the `1.0.0` release.

---

## Version 1.0.0 - Stable Release

-   **🎯 Key Goal**: Mark the library as stable, reliable, and production-ready.
-   **Commitments**:
    -   **Guaranteed API Stability**: The public API will adhere to Semantic Versioning. No breaking changes will be introduced until a `2.0.0` release.
    -   **Finalized Documentation**: The documentation will be complete and up-to-date.
    -   **Thorough Testing**: Confident in the test suite and its coverage of all core features and edge cases.

---

## Post-1.0.0 / Future Ideas

Features to be considered after the stable `1.0.0` release.

-   **Speaker Diarization**: Add support for identifying and labeling different speakers (e.g., `Speaker 1: Hello.`, `Speaker 2: Hi there.`).
-   **Translation Support**: Integrate translation APIs or models to translate subtitles into different languages.
-   **GUI Application**: A simple cross-platform desktop app (e.g., using PyQt) for non-technical users.
-   **Plugin System**: Allow integration with other Automatic Speech Recognition (ASR) models beyond Whisper.
