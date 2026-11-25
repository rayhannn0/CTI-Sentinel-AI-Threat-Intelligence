FROM python:3.12-slim
WORKDIR /workspace
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
CMD ["sleep", "infinity"]
