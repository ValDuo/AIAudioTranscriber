import os
import uuid
from asyncio import tasks
from datetime import datetime

import app as app
from fastapi import HTTPException
from starlette import status
from typing import List

from AIAudioTranscriber.src.transcriber.models.CreateTaskRequest import CreateTaskRequest
from AIAudioTranscriber.src.transcriber.models.TaskInfo import TaskInfo
from AIAudioTranscriber.src.transcriber.models.TaskResponse import TaskResponse
from AIAudioTranscriber.src.transcriber.services.QueueManager import QueueManager
from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus

#очередь задач
queue = QueueManager()

#создаем задачу
@app.post("/api/v1/create_task", response_model=dict, status_code=status.HTTP_200_OK)
async def create_task(request: CreateTaskRequest):
    global task
    is_already_in_queue = await queue.get_existance_in_queue(request.file_path)
    try:
        if is_already_in_queue == False:
            if (not os.path.exists(request.file_path)):  # проверка пути к файлу из 1с

                task = TaskInfo(
                    task_id=str(uuid),
                    status=TaskStatus.PENDING,
                    file_path=request.file_path,
                    created_at=datetime.now()
                )

                # заносим задачу в очередь queue
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
        await queue.fail_task(task.task_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании задачи: {str(e)}"
        )


#получаем задачу по айдишнику
@app.get("/api/v1/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )

    task = queue.get_task(task_id)

    response = TaskResponse(
        task_id=task.task_id,
        status=task.status
    )

    if task.status == TaskStatus.COMPLETED and task.result:
        response.results = task.result
    elif task.status == TaskStatus.FAILED and task.error:
        response.error = task.error



    return response


#получаем очередь всех задач
@app.get("/api/v1/tasks", response_model=List[TaskInfo])
async def list_tasks():
    return queue.get_all_tasks()


# получаем статистику
@app.get("/api/v1/queue/stats")
async def get_queue_stats():
    return queue.get_queue_stats()
