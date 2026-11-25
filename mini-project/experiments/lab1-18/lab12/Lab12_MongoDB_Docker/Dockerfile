FROM python:3.12-slim
WORKDIR /app
COPY requirements-runner.txt .
RUN apt-get update && apt-get install -y --no-install-recommends openssl ca-certificates && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements-runner.txt
COPY . .
CMD ["python", "run_all.py"]
