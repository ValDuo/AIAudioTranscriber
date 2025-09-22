

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:main",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )