ENV DJANGO_SETTINGS_MODULE=config.settings.prod
ENV PYTHONUNBUFFERED=1
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
