# Auto-Subs

**A powerful, local-first library and CLI for video transcription and subtitle generation using Whisper.**

This project is currently in early development.

## Installation

```bash
pip install auto-subs
```

## Usage (CLI)

Get the application version:
```bash
auto-subs --version
```

Generate subtitles from a Whisper JSON output:
```bash
auto-subs generate path/to/transcription.json
```

### Options

- `--output, -o`: Specify the output file path. (Defaults to the same name as the input file)
- `--format, -f`: Choose the output format (`srt`, `ass`, `txt`). (Defaults to `srt`)
- `--max-chars`: Set the maximum characters per subtitle line. (Defaults to `35`)

Example with options:
```bash
auto-subs generate input.json -o subtitles.ass -f ass --max-chars 40
```

## Usage (Library)

You can also use `auto-subs` directly in your Python code. The main entry point is the `generate` function, which takes a transcription dictionary and returns the subtitle content as a string.

```python
import json
from auto_subs import generate

# 1. Load your Whisper-compatible transcription data (as a dict)
with open("path/to/transcription.json", "r", encoding="utf-8") as f:
    transcription_data = json.load(f)

try:
    # 2. Generate SRT content
    srt_content = generate(transcription_data, "srt", max_chars=40)

    # 3. Save the content to a file
    with open("output.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)

    print("Successfully generated subtitles!")

except ValueError as e:
    # Handle validation errors
    print(f"Error: {e}")

```

## API Design Philosophy

### Simplicity for the User: Dictionaries as Input

The public API of `auto-subs` is designed to be as simple and accessible as possible. All functions that process transcription data, like `auto_subs.generate()`, accept a standard Python dictionary (`dict`).

This approach was chosen intentionally to:
- **Reduce friction:** You can directly use the JSON output from Whisper or other tools after loading it into a dictionary, without needing to import and instantiate custom Pydantic models.
- **Decouple your code:** Your project doesn't need to depend on the internal data structures of `auto-subs`. This makes the library easier to integrate and your code more resilient to future updates.

While the input is a simple dictionary, `auto-subs` performs robust internal validation using Pydantic to ensure the data is well-formed before processing it. This gives you the best of both worlds: a simple, clean API and the safety of strong data validation.

### Outputs

The CLI can generate subtitles in the following formats:
- **SRT (.srt)**: The most common subtitle format, compatible with most video players.
- **ASS (.ass)**: Advanced SubStation Alpha, allowing for rich styling (word-level highlighting coming soon).
- **Text (.txt)**: A plain text transcript.

---
*This project is maintained by [Mateusz Kowalski](https://github.com/mateusz-kow).*
