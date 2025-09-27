from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from datetime import datetime
import os

from AIAudioTranscriber.src.transcriber.utils.TaskStatus import TaskStatus




@app.on_event("startup")
async def startup_event():
    """Запуск фоновой задачи при старте приложения"""
    asyncio.create_task(process_tasks())




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


