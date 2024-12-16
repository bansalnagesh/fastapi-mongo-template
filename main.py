import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        workers=4,
        host="127.0.0.1",
        port=3000,
        reload=True,
        timeout_keep_alive=30
    )