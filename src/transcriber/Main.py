from fastapi import FastAPI

#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "main:main",
#         host=settings.HOST,
#         port=settings.PORT,
#         reload=settings.DEBUG,
#         log_level="info" if settings.DEBUG else "warning"
#     )

if __name__ == "__main__":
    import uvicorn
    app = FastAPI(title="Transcription API", version="1.0.0")
    uvicorn.run(app, host="0.0.0.0", port=8080)