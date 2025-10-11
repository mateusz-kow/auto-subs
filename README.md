<div align="center">
  <p>
  </p>
  <br>
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

- **🎯 Intelligent Word Segmentation**: Automatically splits word-level transcriptions into perfectly timed subtitle lines based on character limits and natural punctuation breaks.
- **⚙️ Simple & Powerful API**: Use it as a library with a clean, dictionary-based input that requires no complex objects, or as a feature-rich command-line tool.
- **🛡️ Robust Validation**: Automatically handles common data issues, like inverted timestamps (`start > end`), ensuring your process never breaks on imperfect data.
- **📄 Multiple Formats**: Generate subtitles in the most popular formats: **SRT**, **ASS**, and plain **TXT**.
- **✅ High Quality & Tested**: Strictly typed with Mypy, linted with Ruff, and rigorously tested to ensure reliability.

## Installation

```bash
pip install auto-subs
```

## Quickstart

### As a Command-Line Tool (CLI)

The fastest way to generate a subtitle file from a Whisper-compatible JSON.

```bash
# Generate an SRT file with default settings
auto-subs generate path/to/transcription.json

# Generate a styled ASS file with a custom character limit
auto-subs generate input.json -f ass -o styled.ass --max-chars 42
```

**CLI Options:**
- `--output, -o`: Specify the output file path. (Defaults to the input filename with a new extension)
- `--format, -f`: Choose the output format (`srt`, `ass`, `txt`). (Defaults to `srt`)
- `--max-chars`: Set the maximum characters per subtitle line. (Defaults to `35`)

### As a Python Library

Integrate `auto-subs` directly into your application for full control.

```python
import json
from auto_subs import generate

# 1. Load your Whisper-compatible transcription data (as a dict)
with open("path/to/transcription.json", "r", encoding="utf-8") as f:
    transcription_data = json.load(f)

try:
    # 2. Generate SRT content with a 40-character limit per line
    srt_content = generate(transcription_data, "srt", max_chars=40)

    # 3. Save the content to a file
    with open("output.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)

    print("Successfully generated subtitles!")

except ValueError as e:
    # Handle validation errors for malformed input data
    print(f"Error: {e}")
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
