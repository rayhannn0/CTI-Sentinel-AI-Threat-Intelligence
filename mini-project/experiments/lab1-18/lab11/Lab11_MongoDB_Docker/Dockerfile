FROM python:3.12-slim
WORKDIR /app
COPY requirements-runner.txt .
RUN pip install --no-cache-dir -r requirements-runner.txt
COPY . .
CMD ["python", "run_all.py"]
