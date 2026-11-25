FROM python:3.12-slim
WORKDIR /app
COPY requirements-runner.txt /app/
RUN pip install --no-cache-dir -r requirements-runner.txt
COPY . /app/
CMD ["python", "run_all.py"]
