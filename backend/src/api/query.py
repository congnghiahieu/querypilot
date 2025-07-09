import os

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from src.core.settings import DOWNLOADS_FOLDER

query_router = APIRouter(prefix="/query", tags=["Query"])


@query_router.get("/download")
def download(type: str = Query(..., enum=["csv", "excel", "pdf"])):
    df = pd.DataFrame([{"user": "Alice", "amount": 100}, {"user": "Bob", "amount": 150}])
    file_path = os.path.join(DOWNLOADS_FOLDER, f"result.{type}")

    if type == "csv":
        df.to_csv(file_path, index=False)
    elif type == "excel":
        df.to_excel(file_path, index=False)
    elif type == "pdf":
        # for prototype: export as CSV and rename to PDF
        df.to_csv(file_path.replace("pdf", "csv"), index=False)
        file_path = file_path.replace("pdf", "csv")

    return FileResponse(
        path=file_path, filename=f"result.{type}", media_type="application/octet-stream"
    )
