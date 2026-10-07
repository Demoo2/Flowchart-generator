import os
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import graphviz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from flowchart import flowchart_bytes

ENV = os.getenv("ENV", "development")
MAX_UPLOAD = 5 * 1024 * 1024  # notebooks can be big because they carry output images
MEDIA_TYPES = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}

if ENV == "production":
  app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
  )
else:
  app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=False,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/")
async def route():
  return {"response": "Server up and runnning!"}


@app.post("/create/flowchart")
async def flowchart(
  file: UploadFile,
  lang: Literal["sk", "en"] = "sk",
  format: Literal["png", "svg", "pdf"] = "png",
):
  filename = file.filename or "code.py"
  if not filename.endswith((".py", ".ipynb")):
    raise HTTPException(400, "Upload a .py or .ipynb file")

  data = await file.read()
  if len(data) > MAX_UPLOAD:
    raise HTTPException(413, "File is too big")
  try:
    code = data.decode("utf-8")
  except UnicodeDecodeError:
    raise HTTPException(400, "File is not UTF-8 text")

  try:
    # graphviz is slow CPU work, keep it off the event loop
    image = await run_in_threadpool(flowchart_bytes, code, filename, lang, format)
  except SyntaxError as e:
    raise HTTPException(400, f"Syntax error on line {e.lineno}: {e.msg}")
  except ValueError as e:
    raise HTTPException(400, f"Cannot draw flowchart: {e}")
  except graphviz.ExecutableNotFound:
    raise HTTPException(500, "Graphviz is not installed on the server")

  download_name = quote(f"{Path(filename).stem}.{format}")
  return Response(
    image,
    media_type=MEDIA_TYPES[format],
    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{download_name}"},
  )


@app.post("/create/chart")
async def chart():
  return {"response": "matplot image chart"}
