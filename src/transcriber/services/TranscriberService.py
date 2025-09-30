import tempfile

import whisper
from typing import Optional, List
import os
from datetime import timedelta

from AIAudioTranscriber.src.transcriber.models.Phrase import Phrase
from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult


def convert_segments_to_phrases(whisper_result: dict) -> List[Phrase]:
    phrases = []
    speech_segments = whisper_result.get('segments', [])

    for segment in speech_segments:
        phrase = Phrase(
            start=segment['start'],  # время начала в сек
            end=segment['end'],  # время окончания в сек
            text=segment['text'].strip()
        )
        phrases.append(phrase)

    return phrases


# объединялка текста из фраз в единый
def _combine_all_text(phrases: List[Phrase]) -> str:
    return " ".join(phrase.text for phrase in phrases)


# форматируем для вывода, возврат - массив
def format_segments_for_display(phrases: List[Phrase]) -> List[str]:
    formatted_segments = []
    for i, phrase in enumerate(phrases, 1):
        start_time = str(0) + str(timedelta(seconds=int(phrase.start)))
        end_time = str(0) + str(timedelta(seconds=int(phrase.end)))
        formatted_segment = f"{i}. {start_time} - {end_time}\n{phrase.text}"
        formatted_segments.append(formatted_segment)

    return formatted_segments


def transcribe_audio(file_path: str) -> Optional[TranscriptionResult]:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            #для виспера будет создана временная директория
            os.environ['TEMP'] = temp_dir
            file_path = os.path.abspath(file_path)
            print(f"Абсолютный путь: {file_path}")

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
                text=_combine_all_text(phrases),
                phrases=phrases
            )
            return transcription_result

    except Exception as e:
        print(f"Ошибка транскрибации: {e}")
        return None
