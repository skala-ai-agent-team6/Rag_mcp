FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/app/.venv/bin:$PATH

RUN pip install --no-cache-dir uv==0.11.31

WORKDIR /app
COPY . .
RUN uv sync --locked --no-dev --python 3.11

CMD ["repair-mcp", "serve", "rag", "--transport", "http", "--host", "0.0.0.0", "--port", "8014"]
