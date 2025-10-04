from pydantic import BaseModel
from typing import List, Optional
from AIAudioTranscriber.src.transcriber.models.Phrase import Phrase


class TranscriptionResult(BaseModel):
    phrases: Optional[List[Phrase]]