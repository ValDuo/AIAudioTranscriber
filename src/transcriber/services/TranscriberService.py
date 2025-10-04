import tempfile

import whisper
from typing import Optional, List
import os

from AIAudioTranscriber.src.transcriber.models.Phrase import Phrase
from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult


def split_text_into_intervals(text: str, start_time: float, end_time: float, interval_duration: float = 3.0) -> List[
    Phrase]:
    phrases = []

    if not text.strip():
        return phrases

    total_duration = end_time - start_time
    if total_duration <= 0:
        return phrases

    num_intervals = max(1, int((total_duration + interval_duration - 1) // interval_duration))

    words = text.split()
    if not words:
        return phrases

    words_per_interval = max(1, len(words) // num_intervals)

    current_time = start_time

    for i in range(num_intervals):
        interval_start = current_time
        interval_end = min(current_time + interval_duration, end_time)

        start_word_index = i * words_per_interval
        end_word_index = min((i + 1) * words_per_interval, len(words)) if i < num_intervals - 1 else len(words)

        interval_words = words[start_word_index:end_word_index]
        interval_text = " ".join(interval_words).strip()

        if interval_text:
            phrases.append(Phrase(
                start=interval_start,
                end=interval_end,
                text=interval_text
            ))

        current_time = interval_end
        if current_time >= end_time:
            break

    return phrases


def create_intervals(whisper_result: dict, interval_duration: float = 3.0) -> List[Phrase]:
    phrases = []
    speech_segments = whisper_result.get('segments', [])

    if not speech_segments:
        return phrases

    for segment in speech_segments:
        segment_start = segment['start']
        segment_end = segment['end']
        segment_text = segment['text'].strip()

        if not segment_text:
            continue

        if segment_end - segment_start > interval_duration:
            segment_phrases = split_text_into_intervals(
                segment_text,
                segment_start,
                segment_end,
                interval_duration
            )
            phrases.extend(segment_phrases)
        else:
            phrases.append(Phrase(
                start=segment_start,
                end=segment_end,
                text=segment_text
            ))

    return phrases


def convert_segments_to_phrases(whisper_result: dict) -> List[Phrase]:
    return create_intervals(whisper_result)


def transcribe_audio(file_path: str) -> Optional[TranscriptionResult]:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # для виспера будет создана временная директория
            os.environ['TEMP'] = temp_dir
            file_path = os.path.abspath(file_path)

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")

            supported_formats = ['.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg']
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext not in supported_formats:
                raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")

            model = whisper.load_model("medium")
            result = model.transcribe(file_path)
            phrases = convert_segments_to_phrases(result)

            transcription_result = TranscriptionResult(
                phrases=phrases
            )
            return transcription_result

    except Exception as e:
        print(f"Ошибка транскрибации: {e}")
