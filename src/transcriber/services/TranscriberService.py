# здесь пишем логику работы с whisper
# так же здесь асинхронный вызов методов (пункт 2 функц требов)
import asyncio
import os
import whisper

from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult


async def transcribe_audio(self, file_path: str) -> TranscriptionResult:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    elif not file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise ValueError("Неподдерживаемый формат аудиофайла")

    else:
        model = whisper.load_model("medium")
        result = model.transcribe(file_path)
        result_str = result.join(",")
        #фразы представляются в виде модели Phrase

        # phrases = self.convert_to_phrases(result)
        return TranscriptionResult(text=result_str)




