# Lab 17 – RAG + Vector Index Benchmark (Docker)

## What's included
- Lab 17.1 threat-intelligence document chunking, MongoDB storage, cosine retrieval, optional Atlas `$vectorSearch`, optional Voyage embedding API, optional LLM, MongoDB multi-turn memory.
- Lab 17.2 FAISS local HNSW-vs-IVF experiment, 5,000 synthetic 384D vectors and 100 queries, exact baseline, CSV and latency-recall chart (install matplotlib optionally).
- Six self-contained unit tests.

**Important:** Atlas doesn't document the specified IVF index configuration. The FAISS comparison is **not** an Atlas IVF index benchmark. Offline mode is an educational fallback and does not claim to execute Atlas vector search or generate LLM answers. See `docs/architecture.md`.

## Mac quick start
1. Extract ZIP; `cd ~/Downloads/lab17/Lab17_RAG_Vector_Docker_Submission` (adjust to actual extracted location).
2. `docker compose up --build -d`
3. `docker compose ps` (mongo healthy, app up)
4. `docker compose exec app python -m scripts.lab17_1 seed`
5. `docker compose exec app python -m scripts.lab17_1 demo`
6. `docker compose exec app python -m pytest -q`
7. `docker compose exec app python -m scripts.lab17_2`
8. Benchmark results are saved under `output/lab17_vector_benchmark.csv` (chart generated automatically).

MongoDB Compass: `mongodb://localhost:27020` (other labs can keep their ports).

## Optional real Atlas Vector Search + Voyage embeddings
Configure `MONGO_URI`, `VOYAGE_API_KEY` in an uncommitted `.env` file; **never upload real keys**. You may need to remove the `mongo` dependency for an Atlas-only deployment or keep the local DB as an unused demonstration container. Run `docker compose exec app python -m scripts.lab17_1 seed`; then `docker compose exec app python -m scripts.lab17_1 index-definition`. Create the named vectorSearch index in Atlas (allow index build to complete), then run `docker compose exec app python -m scripts.lab17_1 ask --atlas --question "How can phishing be mitigated?"`. Configure `OPENAI_API_KEY` to use an external LLM; otherwise an explicitly labeled extractive fallback is returned.

## Docker Hub
After verifying all steps: `docker login` then `docker build --platform linux/amd64 -t rayhann094/lab17-rag-vector:latest .` and `docker push rayhann094/lab17-rag-vector:latest`.

**The Docker Hub image contains the Python app only**; the grader must also have `compose.yaml` to bring up MongoDB. Include ZIP/Compose instructions with the PDF.
