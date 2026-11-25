# Chapter 15 - Multi-Tenant TaskTracker (FastAPI + MongoDB + Docker)

Implements **15.1** JWT authentication, tenant-scoped CRUD, admin/user RBAC, MongoDB atomic per-minute rate limiting and compound indexes; **15.2** 5 x 100 seeded tasks, collection-per-tenant migration, no-leakage validation, listing/creation/analytics benchmarking and a recommendation.

## Mac / Docker Desktop: start here

1. Install and open **Docker Desktop**. No Homebrew, `code` CLI, or local Python installation required.
2. Unzip folder; open **Terminal** and type `cd ` (with a space), drag the extracted `Lab15_MultiTenant_Docker` folder into Terminal, then press Enter.
3. Run:
   ```bash
   docker compose up --build -d
   docker compose exec api python -m scripts.seed_users
   docker compose exec api python -m scripts.migrate all
   docker compose exec api python -m scripts.benchmark
   docker compose exec api pytest -q
   ```
4. Open **http://localhost:8000/docs** (Swagger API). Health URL: http://localhost:8000/health
5. To sign in, POST `/auth/token` with the JSON body below, copy `access_token`, press **Authorize** in Swagger and paste the token (depending on Swagger display, enter plain JWT). Task endpoints then use the JWT; no user-provided tenant_id is trusted.

   ```json
   {"username":"alice", "password":"DemoPass123!", "tenant_id":"tenant1"}
   ```
6. POST `/tasks/` using `{"title":"First task", "description":"Demo", "priority":"high"}`; GET `/tasks/`; PATCH `/tasks/{id}`; DELETE `/tasks/{id}`. Try a `tenant2` token and verify you cannot see `tenant1` tasks. `admin` can see all tasks **within their own tenant only**, never other tenants. `alice` and `bob` see only their own tasks.
7. MongoDB Compass connection from the Mac host: `mongodb://localhost:27017` (database: `tasktracker`). MongoDB host name **inside** the Docker network is `mongo`, not `localhost`.

## Script output / validation

`python -m scripts.migrate all` seeds **500** documents across five tenants, copies them to `tasks_tenant1` through `tasks_tenant5`, then checks count, `_id` equality and tenant field across all five. Output should end with `ALL FIVE TENANTS VALIDATED: PASS`. The benchmark prints **measured** medians in milliseconds; timings depend on your machine. `pytest -q` checks role scope and password logic; end-to-end verification requires running the API against MongoDB.

## Data design

Shared collection `tasks`: `_id`, `tenant_id`, `owner_id`, `title`, `description`, `priority`, `status`, `created_at`. Compound indexes `(tenant_id, created_at)` and `(tenant_id, owner_id)`; `users`: `tenant_id`, `username`, `role`, `password_hash`; `rate_limits`: `window_key`, `count`, `expires_at` with TTL. A signed JWT identifies a user, tenant claim is verified against DB and role is read from DB for each call. Unique counter key and atomic `$inc` implement fixed-minute rate limiting. TTL expiry only cleans old windows.

## Design recommendation (Lab 15.2)

**Document-level isolation:** Simple centralized indexes and schema upgrades, efficient all-tenant analytics; preferred when many tenants and regular analytics are required. Always filter by tenant_id. **Collection-per-tenant:** Distinct collections simplify per-tenant access controls and collection administration; can make certain per-tenant operations easier but increases index/migration overhead as tenants grow. Database-per-tenant is generally the stronger choice for truly independent backups/restores and stricter separation. **Performance is workload- and index-dependent**: never assume collection-per-tenant always queries faster. Consult local benchmark output.

## Docker Hub submission

Run in this folder, replacing `YOUR_DOCKERHUB_USERNAME`:

```bash
# Sign in (interactive; do not place your password in scripts)
docker login
# Build for your Mac's native architecture (use --platform linux/amd64 for x86 graders if needed)
docker build --platform linux/amd64 -t YOUR_DOCKERHUB_USERNAME/lab15-tasktracker:latest .
docker push YOUR_DOCKERHUB_USERNAME/lab15-tasktracker:latest
```

Docker Hub URL is **https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/lab15-tasktracker**. Replace the placeholder URL in the PDF before submitting. The image contains the API + scripts, **not MongoDB itself**; demo requires MongoDB separately. The included compose.yaml builds the local API image and starts both containers. For demonstration specifically from a pulled Hub image, modify `compose.yaml` replacing `build: .` under `api:` with `image: YOUR_DOCKERHUB_USERNAME/lab15-tasktracker:latest` and run `docker compose up -d`.

## Security disclaimer

Seed credentials and default JWT secret are **demo-only**. Change passwords/secrets, restrict CORS, enable MongoDB authentication, use HTTPS and apply production security hardening before external deployment. `mongo` is only published to host loopback for this exercise.

## Deliverables

- `app/main.py` - Lab 15.1 + RBAC activity
- `scripts/seed_users.py` - demo users
- `scripts/migrate.py` - Lab 15.2 seed, migrate and validate
- `scripts/benchmark.py` - measured comparisons
- `Dockerfile`, `compose.yaml`, `requirements.txt` - deployment
- `tests/test_logic.py` - local tests
- `Lab15_DockerHub_Submission_Template.pdf` - replace placeholder before upload
