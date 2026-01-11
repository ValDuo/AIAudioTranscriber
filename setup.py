# setup.py
from setuptools import setup, find_packages

setup(
    name="ai-audio-transcriber",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "pydantic",
        "openai-whisper",
        "uvicorn",
        "ffmpeg-python",
        "pytest>=7.0.0",
    ],
    entry_points={
        "console_scripts": [
            "transcribe=ai_audio_transcriber.main:main",
        ],
    },
)