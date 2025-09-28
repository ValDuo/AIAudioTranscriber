import asyncio
import os
import uuid
from asyncio import tasks
from datetime import datetime

from fastapi import FastAPI, HTTPException
from starlette import status
from typing import List

from AIAudioTranscriber.src.transcriber.models.CreateTaskRequest import CreateTaskRequest
from AIAudioTranscriber.src.transcriber.models.TaskInfo import TaskInfo
from AIAudioTranscriber.src.transcriber.models.TaskResponse import TaskResponse
from AIAudioTranscriber.src.transcriber.services.QueueManager import QueueManager
from AIAudioTranscriber.src.transcriber.services.TaskService import process_tasks
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus

# очередь задач
queue = QueueManager()
app = FastAPI(title="Transcription API", version="1.0.0")


#фоновая задача запускает обработчик задач process_tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_tasks(queue))


# создаем задачу
@app.post("/api/v1/create_task", response_model=dict, status_code=status.HTTP_200_OK)
async def create_task(request: CreateTaskRequest):
    is_already_in_queue = await queue.get_existance_in_queue(request.file_path)
    try:
        if is_already_in_queue == False:
            if not os.path.exists(request.file_path):  # проверка пути к файлу из 1с
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Файл не найден"
                )

            task = TaskInfo(
                task_id=str(uuid.uuid4()),
                status=TaskStatus.PENDING,
                file_path=request.file_path,
                created_at=datetime.now()
            )

            await queue.add_task(task)

            return {
                "task_id": task.task_id,
                "status": "accepted",
                "message": "Задача создана"
            }
        else:
            return {
                "task_id": is_already_in_queue,
                "status": "failed",
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
    task = queue.get_task(task_id)
    if task is not None:
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


# получаем очередь всех задач
@app.get("/api/v1/tasks", response_model=List[TaskInfo])
async def list_tasks():
    return queue.get_all_tasks()


# получаем статистику
@app.get("/api/v1/queue/stats")
async def get_queue_stats():
    return queue.get_queue_stats()
