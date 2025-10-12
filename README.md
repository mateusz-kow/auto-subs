<div align="center">
  <p>
  </p>
  <img src="https://github.com/mateusz-kow/auto-subs/blob/main/assets/logo.png?raw=true" alt="Auto-Subs Logo" width="250">
  <h1>Auto-Subs</h1>
  <strong>Effortless Subtitle Generation from Whisper Transcriptions.</strong>
  <p>A powerful, local-first library and CLI for generating subtitles with precise, word-level accuracy.</p>
</div>

<div align="center">

[![PyPI Version](https://img.shields.io/pypi/v/auto-subs?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/auto-subs/)
[![CI Status](https://github.com/mateusz-kow/auto-subs/actions/workflows/ci.yml/badge.svg)](https://github.com/mateusz-kow/auto-subs/actions/workflows/ci.yml)
[![Code Coverage](https://codecov.io/gh/mateusz-kow/auto-subs/graph/badge.svg)](https://codecov.io/gh/mateusz-kow/auto-subs)
<br />
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Types: Mypy](https://img.shields.io/badge/Types-Mypy-blue.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/pypi/l/auto-subs)](https://opensource.org/licenses/MIT)

</div>

---

**Auto-Subs** bridges the gap between raw transcription data and perfectly formatted subtitles. Whether you're a developer integrating transcription into your application or a content creator needing quick subtitles, `auto-subs` provides a robust, simple, and reliable solution.

## Key Features

-   **🚀 End-to-End Transcription**: Go from an audio or video file directly to perfectly timed subtitles in one command.
-   **🔄 Versatile Format Conversion**: Easily convert existing subtitle files between supported formats.
-   **🧠 Intelligent Word Segmentation**: Automatically splits word-level transcriptions into perfectly timed subtitle lines based on character limits and natural punctuation breaks.
-   **📄 Multiple Formats**: Generate and convert subtitles in the most popular formats: **SRT**, **VTT**, and **ASS**.
-   **🎤 Karaoke-Style Highlighting**: Generate word-by-word highlighting (`{\k...}`) for `.ass` files, perfect for music videos or language learning.
-   **🛡️ Robust Validation**: Automatically handles common data issues, like inverted timestamps (`start > end`), ensuring your process never breaks on imperfect data.
-   **⚙️ Simple & Powerful API**: Use it as a library with a clean, dictionary-based input that requires no complex objects, or as a feature-rich command-line tool.

## Installation

```bash
# For subtitle generation and conversion
pip install auto-subs

# To include direct transcription capabilities
pip install auto-subs[transcribe]
```

## Quickstart

### As a Command-Line Tool (CLI)

`auto-subs` provides three powerful commands: `transcribe`, `generate`, and `convert`.

```bash
# 1. Transcribe a media file directly to a VTT subtitle file
auto-subs transcribe video.mp4 -f vtt --model small

# 2. Generate a styled ASS file from an existing transcription JSON
auto-subs generate input.json -f ass -o styled.ass --max-chars 42 --karaoke

# 3. Convert an existing SRT file to ASS format
auto-subs convert subtitles.srt -f ass
```

Each command supports batch processing directories and has more options available via `--help`.

### As a Python Library

Integrate `auto-subs` directly into your application for full control.

```python
import json
from auto_subs import generate, transcribe, load

# --- Generate from existing JSON ---
with open("path/to/transcription.json", "r", encoding="utf-8") as f:
    transcription_data = json.load(f)

try:
    srt_content = generate(transcription_data, "srt", max_chars=40)
    with open("output.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    print("Successfully generated subtitles!")
except ValueError as e:
    print(f"Error: {e}")


# --- Transcribe directly from a media file ---
try:
    vtt_content = transcribe("path/to/video.mp4", "vtt", model_name="base")
    with open("output.vtt", "w", encoding="utf-8") as f:
        f.write(vtt_content)
except ImportError:
    print("Transcription requires 'auto-subs[transcribe]' to be installed.")
except FileNotFoundError:
    print("Media file not found.")


# --- Load and inspect an existing subtitle file ---
try:
    subtitles = load("path/to/existing.srt")
    print(f"Loaded {len(subtitles.segments)} subtitle segments.")
    for segment in subtitles.segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment}")
except (ValueError, FileNotFoundError) as e:
    print(f"Error loading subtitles: {e}")
```

## API Design: Simplicity First

The public API of `auto-subs` is designed to be as simple as possible. All functions, like `auto_subs.generate()`, accept a standard Python dictionary (`dict`).

This approach was chosen intentionally to:
- **Reduce Friction:** You can directly use the JSON output from Whisper after loading it into a dictionary, without needing to import and instantiate our internal Pydantic models.
- **Decouple Your Code:** Your project doesn't need to depend on our internal data structures, making your code more resilient to future updates.

While the input is a simple dictionary, `auto-subs` performs robust internal validation to ensure the data is well-formed, giving you the best of both worlds: a simple API and the safety of strong data validation.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue. If you'd like to contribute code, please open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
