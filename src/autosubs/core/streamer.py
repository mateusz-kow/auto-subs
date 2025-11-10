"""Core module for streaming and parallel transcription."""

import logging
import multiprocessing
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autosubs.core.transcriber import run_transcription
from autosubs.core.vad import extract_audio_and_speech_timestamps

logger = logging.getLogger(__name__)

# --- Chunking Strategy Parameters ---
MAX_CHUNK_DURATION = 30.0  # Ideal maximum duration for a chunk sent to Whisper.


@dataclass
class _SpeechSegment:
    """Represents a segment of speech to be transcribed."""

    start: float
    end: float


@dataclass
class _Task:
    """A task to be processed by a worker, including its index and audio data."""

    index: int
    audio_chunk: Any  # Actually a np.ndarray, but Any to avoid numpy dependency in core models
    start_time: float
    model_name: str


@dataclass
class _Result:
    """A result from a worker, including the index to maintain order."""

    index: int
    transcription: dict[str, Any] | None


class TranscriptionWorker(multiprocessing.Process):
    """A worker process that loads the Whisper model once and processes tasks from a queue."""

    def __init__(self, task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
        """Initializes the worker process."""
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.model = None

    def run(self) -> None:
        """The main loop of the worker process."""
        while True:
            task: _Task | None = self.task_queue.get()
            if task is None:  # Sentinel value to stop the worker
                break

            if self.model is None:
                try:
                    import whisper  # type: ignore

                    self.model = whisper.load_model(task.model_name)
                except Exception as e:
                    logger.error(f"Worker {os.getpid()} failed to load model: {e}")
                    self.result_queue.put(_Result(index=task.index, transcription=None))
                    continue

            transcription = self._transcribe_chunk(task)
            self.result_queue.put(_Result(index=task.index, transcription=transcription))

    def _transcribe_chunk(self, task: _Task) -> dict[str, Any] | None:
        """Transcribes a single audio chunk numpy array using the pre-loaded model."""
        try:
            if self.model:
                result = self.model.transcribe(task.audio_chunk, word_timestamps=True)
                # Offset all timestamps in the result by the segment's start time
                for seg in result.get("segments", []):
                    seg["start"] += task.start_time
                    seg["end"] += task.start_time
                    for word in seg.get("words", []):
                        word["start"] += task.start_time
                        word["end"] += task.start_time
                return result
            return None
        except Exception as e:
            logger.error(f"Failed to transcribe chunk at {task.start_time:.2f}s: {e}")
            return None


def run_streaming_transcription(media_path: Path, model_name: str) -> dict[str, Any]:
    """Transcribes a media file in parallel using an in-memory, VAD-based workflow.

    Args:
        media_path: The path to the media file.
        model_name: The name of the Whisper model to use.

    Returns:
        The complete transcription result as a dictionary.
    """
    logger.info(f"Starting parallel transcription for {media_path.name}...")
    full_audio, sample_rate, speech_timestamps = extract_audio_and_speech_timestamps(media_path)

    if not speech_timestamps:
        logger.warning("No speech detected by VAD. Running a standard transcription as a fallback.")
        return run_transcription(media_path, model_name)

    raw_segments = [
        _SpeechSegment(start=ts["start"] / sample_rate, end=ts["end"] / sample_rate) for ts in speech_timestamps
    ]

    # --- Intelligent Aggregation Logic ---
    # Goal: Create chunks that are as long as possible (up to MAX_CHUNK_DURATION)
    # to provide maximum context to the Whisper model.
    final_chunks: list[_SpeechSegment] = []
    current_chunk_start = raw_segments[0].start
    last_segment_end = raw_segments[0].end

    for i in range(1, len(raw_segments)):
        segment = raw_segments[i]
        potential_duration = segment.end - current_chunk_start

        if potential_duration > MAX_CHUNK_DURATION:
            # The current chunk is full. Finalize it and start a new one.
            final_chunks.append(_SpeechSegment(start=current_chunk_start, end=last_segment_end))
            current_chunk_start = segment.start

        last_segment_end = segment.end

    # Add the last aggregated chunk
    final_chunks.append(_SpeechSegment(start=current_chunk_start, end=last_segment_end))

    logger.info(f"VAD resulted in {len(final_chunks)} context-rich chunks for processing.")

    task_queue: multiprocessing.Queue = multiprocessing.Queue()
    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    num_workers = os.cpu_count() or 1

    workers = [TranscriptionWorker(task_queue, result_queue) for _ in range(num_workers)]
    for worker in workers:
        worker.start()

    for i, segment in enumerate(final_chunks):
        start_sample = int(segment.start * sample_rate)
        end_sample = int(segment.end * sample_rate)
        audio_chunk = full_audio[start_sample:end_sample]
        task = _Task(i, audio_chunk, segment.start, model_name)
        task_queue.put(task)

    for _ in range(num_workers):
        task_queue.put(None)

    results: list[_Result] = []
    for _ in range(len(final_chunks)):
        result = result_queue.get()
        results.append(result)
        logger.info(f"Completed chunk: {len(results)}/{len(final_chunks)}")

    for worker in workers:
        worker.join()

    results.sort(key=lambda r: r.index)
    all_segments = []
    for result in results:
        if result.transcription:
            all_segments.extend(result.transcription.get("segments", []))

    # Re-ID segments and combine text
    full_text = []
    for i, seg in enumerate(all_segments):
        seg["id"] = i
        full_text.append(seg.get("text", "").strip())

    final_transcription = {
        "text": " ".join(full_text),
        "segments": all_segments,
        "language": all_segments[0].get("language", "unknown") if all_segments else "unknown",
    }
    logger.info("Parallel transcription complete.")
    return final_transcription
