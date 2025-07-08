from fastapi import APIRouter

query_router = APIRouter(prefix="/query", tags=["Query"])


@query_router.post("/execute")
def execute_query():
    pass


@query_router.get("/result/{id}")
def get_query_result(id: str):
    pass


@query_router.get("/schema")
def get_schema():
    pass
