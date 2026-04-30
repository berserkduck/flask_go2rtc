FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir pdm \
    && pdm config python.use_venv false \
    && pdm install --production --no-lock

COPY app.py ./
COPY gunicorn.conf.py ./
COPY templates/ ./templates/

RUN mkdir -p /app/data

EXPOSE 80

CMD ["pdm", "run", "gunicorn", "app:app", "-c", "gunicorn.conf.py"]
