from fastapi import FastAPI

from src.api import api_router

app = FastAPI()


@app.get("/")
@app.get("/health")
def health_check():
	return {"status": "ok"}


app.include_router(api_router, prefix="/api", tags=["API"])
