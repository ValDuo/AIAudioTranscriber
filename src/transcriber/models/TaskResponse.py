from typing import Optional

from pydantic import BaseModel

from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    results: Optional[TranscriptionResult] = None
    error: Optional[str] = None
