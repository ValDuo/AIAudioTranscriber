# логика работы с очередью (возможна дальнейшая подвязка БД)
import asyncio
from sqlalchemy.orm import Session

from src.transcriber.services.QueueManager import QueueManager
from src.transcriber.services.TranscriberService import transcribe_audio
from src.transcriber.utils.TaskStatus import TaskStatus

from database import get_db

from config import get_db, TaskDB, TaskStatusEnum


# async def process_tasks(task_queue: QueueManager):
#     while True:
#         try:
#             task = await task_queue.get_next_task()
#             if task is not None:
#                 try:
#                     task.status = TaskStatus.IN_PROGRESS
#                     #задача поступила в работу
#                     transcription_result = await asyncio.to_thread(transcribe_audio, task.file_path)

#                     if transcription_result is None:
#                         raise Exception("Операция транскрибации вернула пустой результат")

#                     await task_queue.complete_task(task.task_id, transcription_result)
#                     print(f"Задача {task.id} успешно обработана")

#                 except Exception as e:
#                     await task_queue.fail_task(task.task_id, str(e))

#         except Exception as e:
#             print(f"Ошибка при выполнении задачи: {e}")

# полностью новый метод для процессинга задач с исп бд
async def process_tasks(task_queue: QueueManager):
    while True:
        try:
            task = await task_queue.get_next_task()
            if task:
                # Обновляем статус в БД на PROCESSING
                db: Session = next(get_db())
                try:
                    db_task = db.query(TaskDB).filter(TaskDB.task_id == task.task_id).first()
                    if db_task:
                        db_task.status = TaskStatusEnum.PROCESSING
                        db.commit()
                except:
                    db.rollback()
                finally:
                    db.close()

                task.status = TaskStatus.IN_PROGRESS

                try:
                    # Выполняем транскрибацию
                    transcription_result = await asyncio.to_thread(transcribe_audio, task.file_path)

                    if transcription_result is None:
                        raise Exception("Транскрибация вернула пустой результат")

                    # Сохраняем результат в БД
                    db: Session = next(get_db())
                    try:
                        db_task = db.query(TaskDB).filter(TaskDB.task_id == task.task_id).first()
                        if db_task:
                            db_task.status = TaskStatusEnum.COMPLETED
                            db_task.results = transcription_result.dict()
                            db.commit()
                    except:
                        db.rollback()
                    finally:
                        db.close()

                    # Обновляем очередь
                    await task_queue.complete_task(task.task_id, transcription_result)
                    print(f"Задача {task.task_id} завершена")

                except Exception as e:
                    # Сохраняем ошибку в БД
                    db: Session = next(get_db())
                    try:
                        db_task = db.query(TaskDB).filter(TaskDB.task_id == task.task_id).first()
                        if db_task:
                            db_task.status = TaskStatusEnum.FAILED
                            db_task.error = str(e)
                            db.commit()
                    except:
                        db.rollback()
                    finally:
                        db.close()

                    # Обновляем очередь
                    await task_queue.fail_task(task.task_id, str(e))
                    print(f"Задача {task.task_id} завершилась с ошибкой: {e}")

        except Exception as e:
            print(f"Ошибка в обработчике задач: {e}")
            await asyncio.sleep(1)