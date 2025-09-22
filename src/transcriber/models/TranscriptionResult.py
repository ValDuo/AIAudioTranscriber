from pydantic import BaseModel
from typing import List

from AIAudioTranscriber.src.transcriber.models.Phrase import Phrase

class TranscriptionResult(BaseModel):
    phrases: List[Phrase]
