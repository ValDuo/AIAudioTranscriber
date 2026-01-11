from typing import Optional

from pydantic import BaseModel

from src.transcriber.models.TranscriptionResult import TranscriptionResult
from src.transcriber.utils.TaskStatus import TaskStatus


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    results: Optional[TranscriptionResult] = None
    error: Optional[str] = None
