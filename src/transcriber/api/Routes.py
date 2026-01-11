import asyncio
import os
import uuid

from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from starlette import status
from typing import List
from sqlalchemy.orm import Session

from src.transcriber.models.CreateTaskRequest import CreateTaskRequest
from src.transcriber.models.TaskInfo import TaskInfo
from src.transcriber.models.TaskResponse import TaskResponse
from src.transcriber.services.QueueManager import QueueManager
from src.transcriber.services.TaskService import process_tasks
from src.transcriber.utils.TaskStatus import TaskStatus

# from config import get_db, TaskDB, TaskStatusEnum, init_db

# очередь задач
queue = QueueManager()

app = FastAPI(title="Transcription API", version="1.0.0")


# фоновая задача запускает обработчик задач process_tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_tasks(queue))


# Вспомогательные функции для конвертации статусов из модели для бд в нашу доменную модель
# def to_db_status(status: TaskStatus) -> TaskStatusEnum:
#     return TaskStatusEnum[status.name]
#
#
# def from_db_status(status: TaskStatusEnum) -> TaskStatus:
#     return TaskStatus[status.name]


# создаем задачу
@app.post("/api/v1/create_task", response_model=dict, status_code=status.HTTP_200_OK)
async def create_task(request: CreateTaskRequest):
    print(f"DEBUG: Получен запрос с file_path: {request.file_path}")
    print(f"DEBUG: Файл существует: {os.path.exists(request.file_path)}")
    is_already_in_queue = await queue.get_existance_in_queue(request.file_path)
    try:
        if not is_already_in_queue:
            if not os.path.exists(request.file_path):  # проверка пути к файлу из 1с
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Файл не найден"
                )

            # ДЛЯ ЛЕРОЧКИ: теперь он добавляет еще и в бд когда все гуд
            # existing_task = db.query(TaskDB).filter(
            #     TaskDB.file_path == request.file_path,
            #     TaskDB.status.in_([TaskStatusEnum.PENDING, TaskStatusEnum.PROCESSING])
            # ).first()

            # if existing_task:
            #     return {
            #         "task_id": existing_task.task_id,
            #         "status": "PENDING",
            #         "message": "Задача уже в обработке"
            #     }

            # Создаем новую задачу
            task_id = str(uuid.uuid4())

            # Сохраняем в БД
            # db_task = TaskDB(
            #     task_id=task_id,
            #     status=TaskStatusEnum.PENDING,
            #     file_path=request.file_path,
            #     created_at=datetime.utcnow()
            # )
            # db.add(db_task)
            # db.commit()

            task = TaskInfo(
                task_id=str(uuid.uuid4()),
                status=TaskStatus.PENDING,
                file_path=request.file_path,
                created_at=datetime.now(tz=None)
            )

            await queue.add_task(task)

            return {
                "task_id": task.task_id,
                "status": task.status,
                "message": "Задача создана"
            }
        else:
            return {
                "task_id": is_already_in_queue,
                "status": "FAILED",
                "message": "Задача с таким путем уже создана"
            }

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании задачи: {str(e)}"
        )


# получаем задачу по айдишнику
@app.get("/api/v1/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
# async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    # Ищем в БД
    # db_task = db.query(TaskDB).filter(TaskDB.task_id == task_id).first()
    #
    # if not db_task:
    #     # Проверяем очередь
    #     task = await queue.get_task(task_id)
    #     if not task:
    #         raise HTTPException(status_code=404, detail="Задача не найдена")
    #
    #     return TaskResponse(
    #         task_id=task.task_id,
    #         status=task.status,
    #         results=task.result if task.status == TaskStatus.COMPLETED else None,
    #         error=task.error if task.status == TaskStatus.FAILED else None
    #     )
    #
    # # Конвертируем из БД
    # response = TaskResponse(
    #     task_id=db_task.task_id,
    #     status=from_db_status(db_task.status)
    # )
    #
    # if db_task.status == TaskStatusEnum.COMPLETED and db_task.results:
    #     # Импортируем здесь, чтобы избежать циклического импорта
    #     from src.transcriber.models.TranscriptionResult import TranscriptionResult
    #     response.results = TranscriptionResult(**db_task.results)
    #
    # elif db_task.status == TaskStatusEnum.FAILED and db_task.error:
    #     response.error = db_task.error
    #
    # return response

    # ДЛЯ ЛЕРОЧКИ: убрал этот код так как теперь достается из бд а не из очереди
    task = await queue.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    response = TaskResponse(
        task_id=task.task_id,
        status=task.status
    )

    if task.status == TaskStatus.COMPLETED and task.result:
        response.results = task.result
    elif task.status == TaskStatus.FAILED and task.error:
        response.error = task.error

    return response


# ДЛЯ ЛЕРОЧКИ: добавлен отдельный метод который достает все данные из бд
# первый метод твой изначальный - второй из бд
# получаем очередь всех задач
@app.get("/api/v1/tasks", response_model=List[TaskInfo])
async def list_tasks_queue():
    return await asyncio.to_thread(queue.get_all_tasks)


# Список всех задач
# @app.get("/api/v1/tasks/db", response_model=list)
# async def list_tasks_db(db: Session = Depends(get_db)):
#     db_tasks = db.query(TaskDB).all()
#
#     result = []
#     for task in db_tasks:
#         task_dict = {
#             "task_id": task.task_id,
#             "status": task.status.value,
#             "file_path": task.file_path,
#             "created_at": task.created_at,
#             "updated_at": task.updated_at
#         }
#
#         if task.results:
#             task_dict["has_results"] = True
#         if task.error:
#             task_dict["error"] = task.error
#
#         result.append(task_dict)
#
#     return result


# получаем статистику
@app.get("/api/v1/queue/stats")
async def get_queue_stats():
    return queue.get_queue_stats()
