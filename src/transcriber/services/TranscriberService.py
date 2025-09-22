#здесь пишем логику работы с whisper
#так же здесь асинхронный вызов методов (пункт 2 функц требов)
import asyncio
import os

from AIAudioTranscriber.src.transcriber.models.Phrase import Phrase
from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult


async def transcribe_audio(file_path: str) -> TranscriptionResult:
    """
    Имитация транскрибации аудио
    В проекте здесь будет интеграция с Whisper, Vosk и т.д.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise ValueError("Неподдерживаемый формат аудиофайла")

    await asyncio.sleep(5)


    phrases = [
        Phrase(start=0.0, end=2.5, text="Здравствуйте, это тестовая запись."),
        Phrase(start=2.7, end=5.2, text="Она будет использована для транскрибации."),
        Phrase(start=5.5, end=8.0, text="Спасибо за использование нашего сервиса.")
    ]

    return TranscriptionResult(phrases=phrases)