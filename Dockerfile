FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем всё
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем пакет
RUN pip install .

EXPOSE 8000

# Запускаем приложение
CMD ["uvicorn", "ai_audio_transcriber.main:app", "--host", "0.0.0.0", "--port", "8000"]
