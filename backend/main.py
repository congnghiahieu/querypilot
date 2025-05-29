from fastapi import FastAPI

app = FastAPI()


@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok"}
