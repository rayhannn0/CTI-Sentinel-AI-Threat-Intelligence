# CTI Sentinel — Appendix A AI Threat Advisor

Adds an LLM/RAG chat application to the existing CTI Sentinel website without replacing its Lab 1–18 pages.

## Install on your Mac

1. Stop the running website (Ctrl+C). Keep the Lab 18 MongoDB container running.
2. Extract the update ZIP in `~/Downloads` (the ZIP contains `NoSQL_Sentinel_18_Labs/`).
3. `cd ~/Downloads/NoSQL_Sentinel_18_Labs && python3 install_advisor.py`
4. Start Ollama separately if you want generated answers: `ollama pull qwen2.5:1.5b` (small local model); `ollama serve` if not already running. Optional for actual semantic embeddings: `ollama pull nomic-embed-text` and set `OLLAMA_EMBED_MODEL=nomic-embed-text` before starting the website; otherwise a deterministic **lexical hashing vector** is used and labeled clearly.
5. `bash start_sentinel.command` and open `http://127.0.0.1:8765/advisor`.
6. Click **Seed Threat Knowledge**, select a platform and lifecycle stage, and ask a question.

If you want a hosted model instead, export `OPENAI_API_KEY=...` in the website Terminal before launching; NEVER commit a real key.

**Dependencies:** Existing FastAPI + PyMongo installation. Optional Ollama uses HTTP and does not require extra Python dependencies.

**Data:** Uses the existing Lab 18 MongoDB server at `127.0.0.1:27021` but writes only to a new `cti_advisor` database, preserving your `threat_intel` and lab databases. Embeddings and source text live in `cti_advisor.knowledge`; conversation history in `cti_advisor.conversations`; TTL rate counters in `cti_advisor.rate_limits`.

**Chat:** `POST /api/advisor/chat` retrieves top-3 relevant chunks scoped by platform/lifecycle, includes up to 6 previous messages, calls local Ollama or hosted OpenAI, then stores the exchange. If no LLM is available, clearly returns retrieval-only guidance. Threat lifecycle classifications are *teaching labels*, and Lab 18 data is synthetic.

**Endpoints:** `/advisor`, `/api/advisor/health`, `/api/advisor/seed`, `/api/advisor/ingest`, `/api/advisor/chat`, `/api/advisor/history`.

**Security:** Designed for a local classroom demonstration. For public hosting, add authenticated users and session ownership, proper TLS, authorization, CORS restrictions, more robust cross-process rate limiting, timeouts, model-cost limits, structured prompt-injection defenses, and security event monitoring. The system never automatically runs system remediation commands.

**Appendix A coverage:** A.1 local LLM + optional hosted API; A.2 chunk and embed ingestion; A.3 FastAPI RAG endpoint; A.4 MongoDB session history; A.5 integrated HTML/JS interface; A.6 companion Docker deployment example; A.7 basic rate limiting, health checks, env-secret handling, no remote exposure. Native Atlas `$vectorSearch` is not available in this local Docker MongoDB setup: this code performs **Python-side exact vector cosine retrieval** over the stored MongoDB vectors, not native Atlas vector search.

**University submission:** Put your complete project in a **private** GitHub repository, confirm the Docker demonstration, provide faculty collaborator access using GitHub repository Settings → Collaborators, and submit a PDF containing the private GitHub repository URL. Do not upload `.env`, passwords, MongoDB data files, model weights, or API keys.

### Optional standalone Docker demo
Run `docker compose -f compose.advisor.yaml up --build -d` from the website folder. Open `http://127.0.0.1:8877/advisor`. This is a separate isolated demonstration stack and does **not** replace your existing CTI Sentinel website or Lab 18 data. Stop it using `docker compose -f compose.advisor.yaml stop`.
