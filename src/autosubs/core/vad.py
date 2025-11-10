"""Core module for Voice Activity Detection using Silero-VAD."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from autosubs.core.burner import FFmpegError

logger = logging.getLogger(__name__)

VAD_SAMPLING_RATE = 16000  # Silero-VAD operates at a 16kHz sample rate


def extract_audio_and_speech_timestamps(media_path: Path) -> tuple[Any, int, list[dict[str, int]]]:
    """Extracts audio as a NumPy array and detects speech segments using Silero-VAD.

    Args:
        media_path: Path to the audio or video file.

    Returns:
        A tuple containing:
        - The audio data as a NumPy array (importantly, in float32 format).
        - The sample rate of the audio.
        - A list of dicts, each with 'start' and 'end' of a speech segment in samples.

    Raises:
        ImportError: If torch, soundfile, or silero-vad are not installed.
        FFmpegError: If ffmpeg fails to extract audio.
    """
    try:
        import numpy as np
        import soundfile as sf
        import torch
    except ImportError as e:
        raise ImportError(
            "Advanced VAD requires 'auto-subs[stream]'. Please install it with: pip install 'auto-subs[stream]'"
        ) from e

    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    (get_speech_timestamps_func, _, _, _, _) = utils

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = Path(temp_dir) / "temp_audio.wav"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(media_path),
            "-ar",
            str(VAD_SAMPLING_RATE),
            "-ac",
            "1",
            "-vn",
            str(wav_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        except (subprocess.CalledProcessError, FileNotFoundError) as err:
            raise FFmpegError("ffmpeg failed to extract audio for VAD processing.") from err

        wav_data, sample_rate = sf.read(str(wav_path))
        assert sample_rate == VAD_SAMPLING_RATE

        # --- FIX: Convert audio data to float32, which Whisper expects ---
        wav_data_float32 = wav_data.astype(np.float32)

        audio_tensor = torch.from_numpy(wav_data).float()
        speech_timestamps = get_speech_timestamps_func(audio_tensor, model, sampling_rate=VAD_SAMPLING_RATE)

    logger.info(f"VAD detected {len(speech_timestamps)} speech segments.")
    return wav_data_float32, sample_rate, speech_timestamps
