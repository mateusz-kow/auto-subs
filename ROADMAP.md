# Auto-Subs Roadmap to 1.0.0

This document outlines the planned features and improvements for `auto-subs` as it progresses towards a stable `1.0.0` release. The goal of `1.0.0` is to provide a mature, feature-rich, and highly reliable tool for subtitle generation and conversion.

This roadmap is a living document and is subject to change based on development progress and community feedback.

## Current State: v0.3.2

-   **Core Functionality**: Transcribe media files, generate subtitles from JSON, and convert between existing subtitle formats.
-   **Supported Formats**: SRT, ASS, VTT.
-   **Features**: Intelligent word segmentation, karaoke-style highlighting for ASS, batch processing, Whisper model selection.
-   **Interfaces**: Python library API (`auto_subs.transcribe`, `auto_subs.generate`, `auto_subs.load`) and a Typer-based CLI.

---

## Version 0.3.3 - Code Quality & Refactoring

This is a maintenance release focused on improving the internal architecture, making the codebase more robust, scalable, and easier to maintain.

-   **🎯 Key Goal**: Refactor the codebase for long-term health and scalability.
-   **Changes**:
    -   **[Major] API & CLI Package Restructuring**:
        -   The `api.py` and `cli.py` modules will be converted into packages (`api/` and `cli/`).
        -   This will break down large files into smaller, single-responsibility modules, improving organization and making testing more granular.
    -   **[Major] Refactor to Factory Pattern**:
        -   Replace `if/elif` chains for format handling (`srt`, `vtt`, `ass`) with a more maintainable factory (dictionary-based) pattern. This makes adding new formats cleaner in the future.
    -   **[Breaking] Remove TXT Output Format**:
        -   The plain text (`.txt`) output format will be removed. It is an outlier as it does not contain timing data, which complicates the API and core logic. Users can still easily produce plain text from any subtitle file.
    -   **Abstract CLI Path Handling Logic**:
        -   Create a shared utility to handle file/directory path processing and batch logic, removing significant code duplication between the `generate`, `transcribe`, and `convert` commands.

---

## Version 0.4.0 - Advanced Customization & Usability

This release will focus on giving users more fine-grained control over the subtitle output and improving the user experience.

-   **🎯 Key Goal**: Empower users with advanced styling and segmentation options.
-   **Features**:
    -   **Advanced ASS Styling**:
        -   **Style Configuration Files**: Introduce a `--style <file.json>` option to load a complete ASS style from a file, allowing users to create, save, and share style presets.
        -   **Optional Default Styling**: Allow `AssSettings` to be completely optional. When not provided, no style block will be embedded, allowing the video player (e.g., FFmpeg, VLC) to apply its own default style.
        -   **Granular CLI Flags**: Expose key `AssSettings` parameters as CLI options for quick, on-the-fly customization (e.g., `--ass-font "Comic Sans"`).
    -   **Enhanced Segmentation Logic**:
        -   Introduce a `--min-words-per-line` option to prevent single-word subtitle lines, which can be visually jarring.
        -   Add a `--max-lines` option (defaulting to 2) to control how many lines a single subtitle entry can have.
    -   **Output Format Inference**:
        -   Allow the CLI to automatically detect the desired output format from the file extension provided in the `--output` flag (e.g., `auto-subs generate in.json -o out.vtt` will automatically select VTT format).

---

## Version 0.5.0 - Robustness and Integration

This release will focus on hardening the tool against edge cases and making the API more flexible for developers.

-   **🎯 Key Goal**: Ensure maximum reliability and improve the developer experience.
-   **Features**:
    -   **Improved Data Validation and Correction**:
        -   Explicitly validate and, where possible, correct inverted timestamps (`start > end`) at the word level, logging a warning instead of failing.
        -   Add checks for overlapping word timestamps within a segment.
    -   **Flexible API Inputs**:
        -   Update API functions to optionally accept a file path (`str` or `Path`) in addition to a dictionary, simplifying common workflows.
    -   **Structured JSON Output**:
        -   Add a new output format: `json`. This format will output the cleaned, validated, and segmented subtitle data as a structured JSON file. This is useful for developers who want to use `auto-subs` as a pre-processing step in a larger toolchain.

---

## The Path to 1.0.0 (v0.6.0 - v0.9.x)

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
