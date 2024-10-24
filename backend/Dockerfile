FROM python:3.9.20-slim

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

RUN adduser --system --group web

USER web

WORKDIR /app

RUN mkdir \
  collected_static \
  media

USER root

RUN --mount=type=cache,target=/root/.cache/pip \
  --mount=type=bind,source=requirements.txt,target=requirements.txt \
  pip install --upgrade pip && \
  pip install -r requirements.txt

COPY . .

USER web

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD [ "gunicorn", "--bind", "0.0.0.0:8000", "project_foodgram.wsgi"]

EXPOSE 8000
