FROM --platform=linux/amd64 python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && curl -fSL https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-100.20.1.deb \
    -o /tmp/mongodb-database-tools.deb \
 && apt-get install -y /tmp/mongodb-database-tools.deb \
 && rm -f /tmp/mongodb-database-tools.deb \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/backups /app/logs /app/output

CMD ["python", "run_all.py"]
