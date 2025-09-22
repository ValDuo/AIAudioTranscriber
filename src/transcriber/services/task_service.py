#логика работы с бд
import asyncio
import datetime
from typing import Dict

from AIAudioTranscriber.src.transcriber.models.TaskInfo import TaskInfo
from AIAudioTranscriber.src.transcriber.utils.task_status import TaskStatus

tasks: Dict[str, TaskInfo] = {}
tasks_queue = asyncio.Queue()
async def process_tasks():
    """Обработчик очереди задач"""
    while True:
        try:
            if not tasks_queue.empty():
                task_id = await tasks_queue.get()
                task = tasks[task_id]

                # Обновляем статус
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now()

                try:
                    # Имитация транскрибации
                    result = await transcribe_audio(task.file_path)
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.completed_at = datetime.now()

                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now()

            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in task processor: {e}")
            await asyncio.sleep(5)
