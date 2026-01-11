from pydantic import BaseModel
from typing import List, Optional
from src.transcriber.models.Phrase import Phrase


class TranscriptionResult(BaseModel):
    phrases: Optional[List[Phrase]]