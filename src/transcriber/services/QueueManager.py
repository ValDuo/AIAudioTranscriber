import uuid
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

from fastapi import HTTPException
from starlette import status

from ..models.CreateTaskRequest import CreateTaskRequest
from ..models.TaskInfo import TaskInfo
from ..models.TranscriptionResult import TranscriptionResult
from ..utils.TaskStatus import TaskStatus


class QueueManager:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._active_tasks: Dict[str, TaskInfo] = {}
        self._completed_tasks: Dict[str, TaskInfo] = {}

    async def add_task(self, task: TaskInfo) -> None:
        await self._queue.put(task)
        await self._active_tasks.put(task)


    async def get_existance_in_queue(self, file_path: str = None) -> bool:
        all_tasks = list(self._active_tasks.values()) + list(self._completed_tasks.values())
        for task in all_tasks:
            if hasattr(task, 'file_path') and task.file_path == file_path:
                return True

        return False

    async def complete_task(self, task_id: str, result: str = None) -> None:
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            self._completed_tasks[task_id] = task
            del self._active_tasks[task_id]

    async def fail_task(self, task_id: str, error: str) -> None:
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.utcnow()
            self._completed_tasks[task_id] = task
            del self._active_tasks[task_id]

    def get_task(self, task_id: str) -> Optional[TranscriptionResult]:
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        elif task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        return None

    def get_all_tasks(self) -> List[TranscriptionResult]:
        all_tasks = list(self._active_tasks.values()) + list(self._completed_tasks.values())
        return all_tasks

    def get_queue_stats(self) -> Dict:
        return {
            "pending": self._queue.qsize(),
            "in_progress": len(self._active_tasks),
            "completed": len(self._completed_tasks)
        }

