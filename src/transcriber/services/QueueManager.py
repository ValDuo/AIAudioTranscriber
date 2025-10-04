from AIAudioTranscriber.src.transcriber.models.TaskInfo import TaskInfo
from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus

from typing import List, Dict, Optional
from datetime import datetime
import asyncio


class QueueManager:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._active_tasks: Dict[str, TaskInfo] = {}
        self._completed_tasks: Dict[str, TaskInfo] = {}

    async def add_task(self, task: TaskInfo) -> None:
        await self._queue.put(task)
        self._active_tasks[task.task_id] = task

    async def get_existance_in_queue(self, file_path: str) -> str | bool:
        all_tasks = list(self._active_tasks.values()) + list(self._completed_tasks.values())
        for task in all_tasks:
            if hasattr(task, 'file_path') and task.file_path == file_path:
                return task.task_id
        return False

    async def complete_task(self, task_id: str, result: TranscriptionResult = None) -> None:
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            self._completed_tasks[task_id] = task
            del self._active_tasks[task_id]

    async def fail_task(self, task_id: str, error: str) -> None:
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now()
            self._completed_tasks[task_id] = task
            del self._active_tasks[task_id]

    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        elif task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        return None

    async def get_next_task(self) -> Optional[TaskInfo]:
        try:
            task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            task.status = TaskStatus.IN_PROGRESS
            return task
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    def get_all_tasks(self) -> List[TaskInfo]:
        all_tasks = list(self._active_tasks.values()) + list(self._completed_tasks.values())
        return all_tasks

    def get_queue_stats(self) -> Dict:
        return {
            "pending": self._queue.qsize(),
            "in_progress": len(self._active_tasks),
            "completed": len(self._completed_tasks)
        }