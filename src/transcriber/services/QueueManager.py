from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from ..models.TaskInfo import TaskInfo
from ..models.TranscriptionResult import TranscriptionResult
from ..utils.TaskStatus import TaskStatus

class QueueManager:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._active_tasks: Dict[int, TaskInfo] = {}
        self._completed_tasks: List[TranscriptionResult] = []
    async def add_task(self, task: TranscriptionResult) -> None:
        task.status = TaskStatus.PENDING
        task.created_at = datetime.utcnow()
        await self._queue.put(task)
        self._active_tasks[task.id] = task
    async def get_next_task(self) -> Optional[TranscriptionResult]:
        try:
            task = await self._queue.get()
            task.status = TaskStatus.IN_PROGRESS
            return task
        except asyncio.QueueEmpty:
            return None

    async def complete_task(self, task_id: int, result: str = None) -> None:
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            self._completed_tasks.append(task)
            del self._active_tasks[task_id]
    async def fail_task(self, task_id: int, error: str) -> None:
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.utcnow()
            self._completed_tasks.append(task)
            del self._active_tasks[task_id]
    def get_queue_stats(self) -> Dict:
        return {
            "pending": self._queue.qsize(),
            "processing": len(self._active_tasks),
            "completed": len(self._completed_tasks)
        }


