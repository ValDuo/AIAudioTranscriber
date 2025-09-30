#логика работы с очередью (возможна дальнейшая подвязка БД)
import asyncio
from datetime import datetime

from AIAudioTranscriber.src import transcriber
from AIAudioTranscriber.src.transcriber.services.QueueManager import QueueManager
from AIAudioTranscriber.src.transcriber.services.TranscriberService import transcribe_audio
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus


async def process_tasks(task_queue: QueueManager): #переделать логику в зависимости от статуса задачи (сделано)
    while True:
        try:
            task = await task_queue.get_next_task()
            if task is not None:
                try:
                    task.status = TaskStatus.IN_PROGRESS
                    #задача поступила в работу
                    transcription_result = await transcribe_audio(task.file_path)

                    if transcription_result is None:
                        raise Exception("Операция транскрибации вернула пустой результат")

                    print(f"Задача {task.id} успешно обработана")
                    task.status = TaskStatus.COMPLETED
                    # задача отработана
                    task.result = transcription_result
                    task.completed_at = datetime.now(tz=None)
                    return transcription_result

                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now(tz=None)

            await asyncio.sleep(2)
        except Exception as e:
            print(f"Ошибка при выполнении задачи: {e}")
            await asyncio.sleep(5)


