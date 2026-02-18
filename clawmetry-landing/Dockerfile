FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8080
ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "30", "--log-level", "info", "--capture-output", "app:app"]
