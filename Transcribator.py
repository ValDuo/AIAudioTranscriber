from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from enum import Enum
import json
from datetime import datetime
import os

app = FastAPI(title="Transcription API", version="1.0.0")


# Модели данных
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Phrase(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionResult(BaseModel):
    phrases: List[Phrase]


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    results: Optional[TranscriptionResult] = None
    error: Optional[str] = None


class CreateTaskRequest(BaseModel):
    file_path: str


class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    file_path: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TranscriptionResult] = None
    error: Optional[str] = None


# Хранилище задач
tasks: Dict[str, TaskInfo] = {}
tasks_queue = asyncio.Queue()


# Фоновая задача для обработки очереди
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


async def transcribe_audio(file_path: str) -> TranscriptionResult:
    """
    Имитация транскрибации аудио
    В реальном проекте здесь будет интеграция с Whisper, Vosk и т.д.
    """
    # Проверка существования файла
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Проверка формата файла
    if not file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise ValueError("Unsupported file format")

    # Имитация обработки
    await asyncio.sleep(5)  # Имитация времени обработки

    # Генерация тестовых данных
    phrases = [
        Phrase(start=0.0, end=2.5, text="Здравствуйте, это тестовая запись."),
        Phrase(start=2.7, end=5.2, text="Она будет использована для транскрибации."),
        Phrase(start=5.5, end=8.0, text="Спасибо за использование нашего сервиса.")
    ]

    return TranscriptionResult(phrases=phrases)


@app.on_event("startup")
async def startup_event():
    """Запуск фоновой задачи при старте приложения"""
    asyncio.create_task(process_tasks())


@app.post("/api/v1/create_task", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_task(request: CreateTaskRequest, background_tasks: BackgroundTasks):
    """
    Создание задачи транскрибации
    """
    try:
        # Валидация файла
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File not found"
            )

        # Создание задачи
        task_id = str(uuid.uuid4())
        task = TaskInfo(
            task_id=task_id,
            status=TaskStatus.PENDING,
            file_path=request.file_path,
            created_at=datetime.now()
        )

        # Сохранение задачи
        tasks[task_id] = task
        await tasks_queue.put(task_id)

        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "Task created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@app.get("/api/v1/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Проверка статуса задачи
    """
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    task = tasks[task_id]

    response = TaskResponse(
        task_id=task.task_id,
        status=task.status
    )

    if task.status == TaskStatus.COMPLETED and task.result:
        response.results = task.result
    elif task.status == TaskStatus.FAILED and task.error:
        response.error = task.error

    return response


@app.get("/api/v1/tasks", response_model=List[TaskInfo])
async def list_tasks():
    """
    Получение списка всех задач
    """
    return list(tasks.values())


@app.delete("/api/v1/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    """
    Удаление задачи
    """
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    del tasks[task_id]
    return None


# Обработчики ошибок
@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)