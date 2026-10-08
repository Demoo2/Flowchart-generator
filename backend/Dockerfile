FROM python:3.11-slim

# Graphviz draws the flowcharts (the pip package is only a wrapper around it).
# Liberation fonts stand in for Helvetica, which the diagrams use.
RUN apt-get update \
 && apt-get install -y --no-install-recommends graphviz fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

ENV ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home appuser
USER appuser
# build matplotlib's font cache now, not on every cold start
RUN python -c "import matplotlib.font_manager"

COPY --chown=appuser . .

# Render sets PORT; 10000 is its default
EXPOSE 10000
# exec: uvicorn gets stop signals directly, so redeploys shut down cleanly
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
