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

                    transcription_result = await asyncio.to_thread(transcribe_audio, task.file_path)

                    if transcription_result is None:
                        raise Exception("Операция транскрибации вернула пустой результат")

                    await task_queue.complete_task(task.task_id, transcription_result)
                    print(f"Задача {task.id} успешно обработана")
                    return transcription_result

                except Exception as e:
                    await task_queue.fail_task(task.task_id, str(e))

        except Exception as e:
            print(f"Ошибка при выполнении задачи: {e}")

