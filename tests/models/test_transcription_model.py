import pytest

from autosubs.models.transcription import (
    SegmentModel,
    TranscriptionModel,
    WordModel,
)


@pytest.fixture
def sample_transcription_model() -> TranscriptionModel:
    """Provides a sample TranscriptionModel for testing."""
    words = [
        WordModel(word="Hello", start=0.0, end=0.5),
        WordModel(word="world", start=0.5, end=1.0),
    ]
    segments = [
        SegmentModel(
            id=0,
            start=0.0,
            end=1.0,
            text="Hello world",
            words=words,
            seek=10,
            tokens=[1, 2],
            temperature=0.0,
            avg_logprob=-0.1,
            compression_ratio=1.0,
            no_speech_prob=0.0,
        )
    ]
    return TranscriptionModel(
        text="Hello world",
        segments=segments,
        language="en",
    )


def test_transcription_model_to_dict(
    sample_transcription_model: TranscriptionModel,
) -> None:
    """Test that TranscriptionModel.to_dict returns a correct dictionary."""
    transcription_dict = sample_transcription_model.to_dict()

    # Check top-level keys
    assert "text" in transcription_dict
    assert "segments" in transcription_dict
    assert "language" in transcription_dict

    # Check top-level values
    assert transcription_dict["text"] == "Hello world"
    assert transcription_dict["language"] == "en"
    assert isinstance(transcription_dict["segments"], list)
    assert len(transcription_dict["segments"]) == 1

    # Check segment contents
    segment = transcription_dict["segments"][0]
    assert segment["id"] == 0
    assert segment["start"] == 0.0
    assert segment["end"] == 1.0
    assert segment["text"] == "Hello world"
    assert isinstance(segment["words"], list)
    assert len(segment["words"]) == 2

    # Check word contents
    first_word = segment["words"][0]
    assert first_word["word"] == "Hello"
    assert first_word["start"] == 0.0
    assert first_word["end"] == 0.5

    second_word = segment["words"][1]
    assert second_word["word"] == "world"
    assert second_word["start"] == 0.5
    assert second_word["end"] == 1.0
