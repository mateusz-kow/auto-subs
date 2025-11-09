<div align="center">
  <p>
  </p>
  <img src="https://github.com/mateusz-kow/auto-subs/blob/main/assets/logo.png?raw=true" alt="Auto-Subs Logo" width="250">
  <h1>Auto-Subs</h1>
  <strong>Effortless Subtitle Generation from Whisper Transcriptions.</strong>
  <p>A powerful, local-first library and CLI for generating and editing subtitles with precise, word-level accuracy.</p>
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
-   **🔥 Hardsubbing (Video Burning)**: Burn generated subtitles directly into a video file with a simple `--burn` flag.
-   **📝 Rich Programmatic Editing**: A powerful, in-memory API to programmatically edit subtitles—shift timing, adjust duration, merge/split segments, and more.
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

# To include direct transcription and burning capabilities
pip install auto-subs[transcribe]
```

*Hardsubbing requires [FFmpeg](https://ffmpeg.org/download.html) to be installed and available in your system's PATH.*

## Quickstart

### As a Command-Line Tool (CLI)

`auto-subs` provides four powerful commands: `transcribe`, `generate`, `convert`, and `burn`.

> **Note:** Global options like `-q` (quiet) or `-v` (verbose) must be placed *before* the command name (e.g., `auto-subs -q transcribe ...`).

```bash
# 1. Transcribe a video and burn the subtitles directly into a new file
auto-subs transcribe video.mp4 --model small --burn

# 2. Generate a styled ASS file from an existing transcription JSON
auto-subs generate input.json -f ass -o styled.ass --max-chars 42 --karaoke

# 3. Convert an existing SRT file to ASS format
auto-subs convert subtitles.srt -f ass

# 4. Burn an existing subtitle file into a video
auto-subs burn video.mp4 styled.ass -o final_video.mp4
```

### As a Python Library

Integrate `auto-subs` directly into your application for full control.

```python
import json
from autosubs import generate, transcribe, load

# --- Generate from existing JSON ---
with open("path/to/transcription.json", "r", encoding="utf-8") as f:
    transcription_data = json.load(f)

srt_content = generate(transcription_data, "srt", max_chars=40)
with open("output.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)

# --- Transcribe directly from a media file ---
try:
    vtt_content = transcribe("path/to/video.mp4", "vtt", model_name="base")
    with open("output.vtt", "w", encoding="utf-8") as f:
        f.write(vtt_content)
except ImportError:
    print("Transcription requires 'auto-subs[transcribe]' to be installed.")

# --- Load and inspect an existing subtitle file ---
subtitles = load("path/to/existing.srt")
print(f"Loaded {len(subtitles.segments)} subtitle segments.")
```

## Powerful Programmatic Editing

`auto-subs` provides a rich, object-oriented API for advanced, in-memory subtitle manipulation. Once you load or create subtitles, you can edit them and then generate the final output.

```python
from autosubs import load, to_ass
from autosubs.models import AssSettings, AssStyleSettings

# Load an SRT file and automatically generate word-level timings.
# This "upgrades" a standard SRT to a rich, editable format with precise
# word timestamps, enabling fine-grained edits or karaoke generation.
subs = load("input.srt", generate_word_timings=True)

# Get the first subtitle segment
first_segment = subs.segments[0]

# Perform edits using a fluent, chainable API
first_segment.shift_by(-0.25).set_duration(3.5, anchor="start") # Shift 250ms earlier and set duration to 3.5s

# Merge the second and third segments into one
if len(subs.segments) >= 3:
    subs.merge_segments(1, 2)

# Generate a karaoke-style ASS file from the edited subtitles
ass_settings = AssSettings(highlight_style=AssStyleSettings())
karaoke_ass = to_ass(subs, ass_settings)

with open("output.ass", "w") as f:
    f.write(karaoke_ass)
```

## API Design: Simplicity First

The public API of `auto-subs` is designed to be as simple as possible. Functions like `auto_subs.generate()` accept a standard Python dictionary (`dict`).

This approach was chosen intentionally to:
- **Reduce Friction:** You can directly use the JSON output from Whisper after loading it, without needing to instantiate our internal Pydantic models.
- **Decouple Your Code:** Your project doesn't need to depend on our internal data structures, making your code more resilient to future updates.

While the input is simple, `auto-subs` performs robust internal validation, giving you the best of both worlds: a simple API and the safety of strong data validation.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue. If you'd like to contribute code, please open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
