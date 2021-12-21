# syntax = docker/dockerfile:1.2
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN addgroup --system app && adduser --system --group app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install --requirement requirements.txt --no-deps

ENV PYTHONPATH /app
COPY reddit_notifier/ /app/reddit_notifier/

USER app

CMD ["python", "reddit_notifier"]
