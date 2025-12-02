# Auto-Subs Roadmap to 1.0.0

This document outlines the planned features and improvements for `auto-subs` as it progresses towards a stable `1.0.0` release. The goal is to provide a mature, feature-rich, and highly reliable tool for subtitle generation, serving both as a powerful CLI and a definitive developer library.

This roadmap is a living document and is subject to change based on development progress and community feedback.

---

### Core Features (Completed)

These features form the stable foundation of `auto-subs` and are available today.

-   **✅ End-to-End Transcription**: Go from an audio/video file directly to subtitles in a single command.
-   **✅ Hardsubbing (Video Burning)**: Burn generated subtitles directly into a new video file using FFmpeg.
-   **✅ Progress Feedback for Long Transcriptions**: A `--stream` flag provides a real-time activity indicator for long transcription jobs, improving user experience.
-   **✅ Rich Programmatic Editing API**: A powerful, in-memory object model for subtitle manipulation, including methods to `shift_by()`, `resize()`, `set_duration()`, `merge_segments()`, and `split_segment_at_word()`.
-   **✅ Versatile Format Conversion**: Convert between SRT, VTT, and ASS formats.
-   **✅ Intelligent Word Segmentation**: Generate perfectly timed, multi-line subtitle segments from word-level timestamps.
-   **✅ Broad Format Support**: Full support for SRT, VTT, ASS, and a Whisper-compatible JSON format.
-   **✅ Karaoke-Style Highlighting**: Generate word-by-word `{\k...}` timing tags for ASS files.
-   **✅ Robust Data Validation**: Automatically handle inverted timestamps and warn about overlapping segments.
-   **✅ Simple & Powerful API**: A clean, dictionary-based API that also accepts file paths for maximum flexibility.
-   **✅ Batch Processing**: Process entire directories of media or transcription files with a single command.
-   **✅ Advanced ASS Styling Engine**: A modular, rule-based styling engine for `.ass` files with Pydantic-validated configuration, enabling dynamic, time-aware, and layered styling effects.

---

### Next Priorities

These are the high-impact features planned for upcoming releases to significantly expand the library's capabilities.

### Future Goals & Advanced Features

These features are aimed at achieving feature parity with established tools and introducing unique, powerful capabilities.

-   **🎯 Advanced Retiming and Utilities**: Add powerful retiming capabilities like `transform_framerate()` and `map_timestamps(func)` for non-linear adjustments.
-   **🎯 Strategic Format Expansion**: Add parsers and writers for other key subtitle formats like **TTML** and the frame-based **MicroDVD (`.sub`)** format for broader compatibility.
-   **🎯 Handling ASS Attachments**: Implement logic to read, store, and write back `[Fonts]` and `[Graphics]` sections from ASS files for full Aegisub compatibility.
-   **🎯 Advanced Styling and Tag Support**: Preserve unknown ASS tags during parsing and implement style management methods like `import_styles()` and `rename_style()`.
-   **🎯 Performance Optimization with Rust**: Post-1.0, investigate rewriting performance-critical, CPU-bound "hot paths" (e.g., subtitle parsing, timestamp math) in Rust using PyO3 for near-native speed, where profiling shows a clear benefit.

### Polish & Production Readiness

These tasks are focused on making the library stable, easy to use, and production-ready for the `1.0.0` release.

-   **🎯 Comprehensive Documentation**: Create a full-fledged documentation website using MkDocs or Sphinx, with a complete API reference, tutorials, and detailed CLI explanations.
-   **🎯 Performance & Optimization**: Profile and optimize all core operations to ensure the library is fast and memory-efficient, even with very large files.
-   **🎯 Release Candidate Phase**: Freeze the API and focus exclusively on bug fixes, performance tweaks, and community feedback in preparation for the stable release.

### Version 1.0.0: Stable Release

-   **🎯 Goal**: Mark the library as stable, reliable, and production-ready, with a guaranteed stable API, finalized documentation, and thorough test coverage.
