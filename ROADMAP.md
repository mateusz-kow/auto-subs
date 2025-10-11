# Auto-Subs Roadmap to 1.0.0

This document outlines the planned features and improvements for `auto-subs` as it progresses towards a stable `1.0.0` release. The goal of `1.0.0` is to provide a mature, feature-rich, and highly reliable tool for subtitle generation and conversion, serving both as a powerful CLI and as the definitive library for building modern, AI-driven subtitle applications.

This roadmap is a living document and is subject to change based on development progress and community feedback.

---

### Phase 1: Solidifying the Foundation (v0.3.x - v0.5.x)

This phase focuses on code quality, usability, and making the existing features more robust.

#### **Version 0.4.0 - Advanced Customization**
-   **🎯 Key Goal**: Empower users with advanced styling and segmentation options.
-   **Features**: Advanced ASS styling (from file, granular CLI flags), enhanced segmentation logic (`--min-words-per-line`, `--max-lines`), CLI output format inference.

#### **Version 0.5.0 - Robustness & Integration**
-   **🎯 Key Goal**: Ensure maximum reliability and improve the developer experience for integrations.
-   **Features**: Improved data validation (inverted/overlapping timestamps), flexible API inputs (accept file paths), serializable models with a dedicated `json` export format, expose core utilities like timestamp formatters.

---

### Phase 2: Achieving Feature Parity and Superiority (v0.6.0 - v0.15.x)

This phase is about closing the gap with established libraries on essential features, while leveraging our unique word-level model to provide superior implementations.

#### **Version 0.6.0 - Rich API for Programmatic Editing**
-   **🎯 Key Goal**: Enable advanced, in-memory subtitle manipulation, a core requirement for GUI editors.
-   **Features**: Mutable `Subtitle` objects with methods like `add_word()`, `remove_segment()`, `merge_segments()`, `split_at_word()`, and `resize()` with **proportional word timestamp scaling**.

#### **Version 0.8.0 - Streaming & Parallel Transcription**
-   **🎯 Key Goal**: Enable real-time feedback and faster processing for long media files, inspired by `agermanidis-autosub` and user feedback.
-   **Features**:
    -   **New `stream_transcribe()` API**: An async generator that yields segments as they are processed.
    -   **Voice Activity Detection (VAD)**: Integrate a modern VAD model to intelligently chunk audio at silent intervals, ensuring high-quality transcription across boundaries.
    -   **Multi-Process Parallelization**: Use a pool of worker processes to transcribe audio chunks in parallel, dramatically reducing total transcription time.

#### **Version 0.10.0 - Advanced Retiming and Utilities**
-   **🎯 Key Goal**: Match and exceed `pysubs2`'s retiming capabilities.
-   **Features**: `transform_framerate()`, `map_timestamps(func)` for non-linear retiming, and a `clean()` method to programmatically remove unwanted content.

#### **Version 0.12.0 - Translation Integration**
-   **🎯 Key Goal**: Provide a flexible, integrated translation workflow.
-   **Features**:
    -   Introduce a `subtitles.translate(dest_lang, backend='google')` method.
    -   Implement a pluggable backend system for different translation services.
    -   CLI integration: `auto-subs transcribe video.mp4 --translate de`.

#### **Version 0.14.0 - CLI Power-User Features**
-   **🎯 Key Goal**: Add high-value, end-to-end features to the CLI.
-   **Features**:
    -   **Hardsubbing**: Introduce a `--burn` flag to the `transcribe` and `generate` commands. This will use FFmpeg to burn the generated subtitles directly into a new video file, a core feature of `m1guelpf-auto-subtitle`.
    -   **Audio Pre-processing Hooks**: Allow specifying simple pre-processing filters (e.g., `--audio-filter "lowpass=3000,highpass=200"`) for advanced users.

#### **Version 0.15.0 - Strategic Format Expansion**
-   **🎯 Key Goal**: Expand support to other key subtitle formats for broader compatibility.
-   **Features**: Add parsers and writers for **TTML** and the frame-based **MicroDVD (`.sub`)** format.

---

### Phase 3: Polish and Production Readiness (v0.16.0 - v0.25.x)

This phase is dedicated to stabilization, documentation, and the final features needed for a world-class library.

#### **Version 0.16.0 - Advanced Styling and Tag Support**
-   **🎯 Key Goal**: Handle complex ASS styling and override tags gracefully.
-   **Features**: Preserve unknown ASS tags, implement `import_styles()` and `rename_style()`.

#### **Version 0.18.0 - Comprehensive Documentation**
-   **🎯 Key Goal**: Create a full-fledged documentation website.
-   **Features**: Set up a site using MkDocs/Sphinx with a full API reference, tutorials, and detailed CLI explanations.

#### **Version 0.20.0 - Performance & Optimization**
-   **🎯 Key Goal**: Ensure the library is fast and memory-efficient with large files.
-   **Features**: Profile and optimize all core operations.

#### **Version 0.22.0 - Handling ASS Attachments**
-   **🎯 Key Goal**: Support preserving embedded data in ASS files for full Aegisub compatibility.
-   **Features**: Implement logic to read, store, and write back `[Fonts]` and `[Graphics]` sections from ASS files.

#### **Version 0.25.0 - Release Candidate Phase**
-   **🎯 Key Goal**: Prepare for the stable release.
-   **Features**: Freeze the API. Focus exclusively on bug fixes, performance tweaks, and community feedback.

---

## Version 1.0.0 - Stable Release

-   **🎯 Key Goal**: Mark the library as stable, reliable, and production-ready for both CLI users and application developers.
-   **Commitments**: Guaranteed API Stability, finalized documentation, and thorough test coverage.
