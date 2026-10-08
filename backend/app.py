import logging
import os
import subprocess
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import graphviz
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from chart import COMPLEXITIES, chart_bytes
from flowchart import flowchart_bytes

ENV = os.getenv("ENV", "development")
# comma-separated website addresses allowed to call the API, e.g. "https://flowchart.pages.dev"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
MAX_UPLOAD = 5 * 1024 * 1024  # notebooks can be big because they carry output images
MEDIA_TYPES = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}
MAX_TEXT = 120  # chart title / labels; long texts take matplotlib very long to draw

logger = logging.getLogger("uvicorn.error")

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
  allow_origins=ALLOWED_ORIGINS,
  allow_credentials=False,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/")
async def route():
  return {"response": "Server up and runnning!"}


@app.get("/health")
async def health():
  return {"status": "ok"}


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
    image = await run_in_threadpool(flowchart_bytes, code, filename, lang, format)
  except SyntaxError as e:
    raise HTTPException(400, f"Syntax error on line {e.lineno}: {e.msg}")
  except ValueError as e:
    raise HTTPException(400, f"Cannot draw flowchart: {e}")
  except graphviz.ExecutableNotFound:
    raise HTTPException(500, "Graphviz is not installed on the server")
  except subprocess.TimeoutExpired:
    raise HTTPException(413, "This code is too big to draw. Try a smaller file.")
  except Exception:
    # HTTPException keeps the CORS headers, so the website can show the message
    logger.exception("Flowchart failed for %s", filename)
    raise HTTPException(500, "Something went wrong while drawing the flowchart")

  download_name = quote(f"{Path(filename).stem}.{format}")
  return Response(
    image,
    media_type=MEDIA_TYPES[format],
    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{download_name}"},
  )


class ChartRequest(BaseModel):
  x: list[float] = Field(min_length=2, max_length=1000)  # input sizes
  y: list[float] = Field(min_length=2, max_length=1000)  # measured steps for each size
  time_complexity: Literal[tuple(COMPLEXITIES)] = "O(n)"
  time_chart: bool = True  # draw the scaled Big-O reference curve
  title: str = Field("", max_length=MAX_TEXT)
  x_label: str = Field("", max_length=MAX_TEXT)
  y_label: str = Field("", max_length=MAX_TEXT)
  label: str = Field("", max_length=MAX_TEXT)
  format: Literal["png", "svg", "pdf"] = "png"


@app.post("/create/chart")
async def chart(request: ChartRequest):
  if len(request.x) != len(request.y):
    raise HTTPException(400, "x and y must have the same number of values")

  try:
    image = await run_in_threadpool(
      chart_bytes,
      request.x,
      request.y,
      request.time_complexity,
      request.time_chart,
      request.title,
      request.x_label,
      request.y_label,
      request.label,
      request.format,
    )
  except Exception:
    logger.exception("Chart failed")
    raise HTTPException(500, "Something went wrong while drawing the chart")
  return Response(
    image,
    media_type=MEDIA_TYPES[request.format],
    headers={"Content-Disposition": f'attachment; filename="chart.{request.format}"'},
  )
