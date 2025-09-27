#логика работы с очередью (возможна дальнейшая подвязка БД)
import asyncio
import datetime
from AIAudioTranscriber.src.transcriber.services.QueueManager import QueueManager
from AIAudioTranscriber.src.transcriber.services.TranscriberService import transcribe_audio
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus

task_queue = QueueManager()
async def process_tasks():
    while True:
        try:
            if not task_queue.empty():
                task_id = await task_queue.get()
                task = task_queue[task_id]

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

            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error in task processor: {e}")
            await asyncio.sleep(5)
