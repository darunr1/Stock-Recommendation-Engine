FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN useradd --create-home --uid 10001 equitylens
COPY apps/api /app/apps/api
COPY config /app/config
COPY scripts /app/scripts
COPY alembic.ini /app/alembic.ini
RUN python -m pip install --upgrade pip && python -m pip install /app/apps/api

RUN mkdir -p /app/var /app/captured-emails && chown -R equitylens:equitylens /app
USER equitylens
ENV PYTHONPATH=/app/apps/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
