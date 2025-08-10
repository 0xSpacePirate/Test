FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir psycopg2-binary

COPY . .

CMD ["python", "main.py"]
