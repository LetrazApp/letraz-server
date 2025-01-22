FROM python:3.12-slim
LABEL authors="arnab"
VOLUME /letraz
WORKDIR /letraz
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . .
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync
RUN uv add gunicorn
RUN python manage.py collectstatic --noinput
EXPOSE 8000
ENTRYPOINT ["gunicorn", "letraz_server.wsgi:application", "--bind", "0.0.0.0:8000"]
#CMD ["python manage.py runserver 0.0.0.0:8000"]