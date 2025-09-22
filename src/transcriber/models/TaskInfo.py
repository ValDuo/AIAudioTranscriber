from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus


class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    file_path: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TranscriptionResult] = None
    error: Optional[str] = None