# Auto-Subs Roadmap to 1.0.0

This document outlines the planned features and improvements for `auto-subs` as it progresses towards a stable `1.0.0` release. The goal is to provide a mature, feature-rich, and highly reliable tool for subtitle generation, serving both as a powerful CLI and a definitive developer library.

This roadmap is a living document and is subject to change based on development progress and community feedback.

---

### Core Features (Completed)

These features form the stable foundation of `auto-subs` and are available today.

-   **✅ End-to-End Transcription**: Go from an audio/video file directly to subtitles in a single command.
-   **✅ Rich Programmatic Editing API**: A powerful, in-memory object model for subtitle manipulation, including methods to `shift_by()`, `resize()`, `set_duration()`, `merge_segments()`, and `split_segment_at_word()`.
-   **✅ Versatile Format Conversion**: Convert between SRT, VTT, and ASS formats.
-   **✅ Intelligent Word Segmentation**: Generate perfectly timed, multi-line subtitle segments from word-level timestamps.
-   **✅ Broad Format Support**: Full support for SRT, VTT, ASS, and a Whisper-compatible JSON format.
-   **✅ Karaoke-Style Highlighting**: Generate word-by-word `{\k...}` timing tags for ASS files.
-   **✅ Robust Data Validation**: Automatically handle inverted timestamps and warn about overlapping segments.
-   **✅ Simple & Powerful API**: A clean, dictionary-based API that also accepts file paths for maximum flexibility.
-   **✅ Batch Processing**: Process entire directories of media or transcription files with a single command.
-   **✅ Advanced ASS Styling**: Customize ASS output using a style file or granular CLI flags.

---

### Next Priorities

These are the high-impact features planned for upcoming releases to significantly expand the library's capabilities.

-   **🎯 Hardsubbing (Video Burning)**: Introduce a `--burn` flag to the `transcribe` and `generate` commands. This will use FFmpeg to burn the generated subtitles directly into a new video file.
-   **🎯 Translation Integration**: Provide a flexible, integrated translation workflow. This will include a `subtitles.translate(dest_lang)` method with a pluggable backend system and a `--translate` flag for the CLI.
-   **🎯 Streaming & Parallel Transcription**: Enable real-time feedback and dramatically faster processing for long media files. This involves a `stream_transcribe()` API, **Voice Activity Detection (VAD)** for intelligent chunking, and multi-process parallelization.

### Future Goals & Advanced Features

These features are aimed at achieving feature parity with established tools and introducing unique, powerful capabilities.

-   **🎯 Context-Aware & Time-Aware Layered Styling Engine**: Introduce a modular, rule-based, and time-aware styling engine to enable Aegisub-level visual fidelity with modern, programmable control, establishing `auto-subs` as a true subtitle generation engine.
-   **🎯 Advanced Retiming and Utilities**: Add powerful retiming capabilities like `transform_framerate()` and `map_timestamps(func)` for non-linear adjustments.
-   **🎯 Strategic Format Expansion**: Add parsers and writers for other key subtitle formats like **TTML** and the frame-based **MicroDVD (`.sub`)** format for broader compatibility.
-   **🎯 Handling ASS Attachments**: Implement logic to read, store, and write back `[Fonts]` and `[Graphics]` sections from ASS files for full Aegisub compatibility.
-   **🎯 Advanced Styling and Tag Support**: Preserve unknown ASS tags during parsing and implement style management methods like `import_styles()` and `rename_style()`.

### Polish & Production Readiness

These tasks are focused on making the library stable, easy to use, and production-ready for the `1.0.0` release.

-   **🎯 Comprehensive Documentation**: Create a full-fledged documentation website using MkDocs or Sphinx, with a complete API reference, tutorials, and detailed CLI explanations.
-   **🎯 Performance & Optimization**: Profile and optimize all core operations to ensure the library is fast and memory-efficient, even with very large files.
-   **🎯 Release Candidate Phase**: Freeze the API and focus exclusively on bug fixes, performance tweaks, and community feedback in preparation for the stable release.

#### **Version 0.17.0 - Context-Aware & Time-Aware Layered Styling Engine**
-   **🎯 Key Goal**: Introduce a modular, rule-based, and time-aware styling engine that enables Aegisub-level visual fidelity with modern, programmable control, establishing `auto-subs` as a true subtitle generation engine.
-   **Features**:
    -   **Layered Styling System**: Implement independent, composable layers for `ass_style` (line appearance), `karaoke_styles` (word timing), and `animation_presets` (reusable `\t` effects).
    -   **Rule-Based & Time-Aware Matching**: Allow styles and animations to be applied based on rules with `patterns` (regex), `priority`, and `start_time`/`end_time` ranges, enabling effects to change dynamically throughout the media.
    -   **Declarative Configuration**: Define all styling logic in a single, validated JSON or YAML file, separating style from content. The engine will use Pydantic for robust validation and convert to internal dataclasses for high performance.
    -   **Indexed Word Architecture**: Internally, each word will reference its applied styles, enabling highly efficient `O(m)` updates, crucial for future GUI applications.
    -   **Dynamic Default Styles**: Support changing the default ASS style for new lines at different points in time, without affecting previously generated lines.

### Version 1.0.0: Stable Release

-   **🎯 Goal**: Mark the library as stable, reliable, and production-ready, with a guaranteed stable API, finalized documentation, and thorough test coverage.
