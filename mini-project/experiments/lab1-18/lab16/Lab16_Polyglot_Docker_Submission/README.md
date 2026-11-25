# Lab 16 — Polyglot Persistence (MongoDB + Cassandra + Neo4j)

Implements **16.1**, the **16.1 Try It Yourself hybrid architecture**, and **16.2** with Docker, seeded sample data, pooled drivers, a circuit breaker, unit tests, integration tests, and latency measurements.

## Requirements
Docker Desktop for Apple Silicon / Mac (allocate at least **6 GB** memory, preferably 8 GB). Cassandra can take several minutes to become healthy. This project is independent of your Lab 15 containers.

## Step-by-step (Mac Terminal)
```bash
cd ~/Downloads/Lab16_Polyglot_Docker
# Make sure this directory contains compose.yaml and Dockerfile
docker compose up --build -d
docker compose ps
```
Wait until `mongo`, `cassandra`, and `neo4j` show healthy and `app` shows up; if Cassandra is not healthy yet, inspect `docker compose logs --tail=40 cassandra` and repeat `docker compose ps` later.

Run in order:
```bash
docker compose exec app python -m scripts.seed
docker compose exec app python -m scripts.lab16_1
docker compose exec app pytest -q
docker compose exec app python -m scripts.lab16_2
```
Expected markers: `SEED COMPLETE`, `LAB 16.1 COMPLETE`, `6 passed`, `LAB 16.2 INTEGRATION PASS`. Actual timings vary.

## Database access
- MongoDB Compass (host): `mongodb://localhost:27019` (database `lab16`)
- Neo4j Browser: http://localhost:7475 (user `neo4j`, password `lab16password`)
- Cassandra via Docker: `docker compose exec cassandra cqlsh`; then `DESCRIBE KEYSPACES;` or `SELECT * FROM university.student_courses WHERE student_id='s1';`
- Do **not** use `localhost` for drivers running inside Docker. They connect to `mongo:27017`, `cassandra:9042`, `neo4j:7687`.

## Demo commands
```bash
docker compose exec mongo mongosh lab16 --quiet --eval 'db.students.find().pretty()'
docker compose exec cassandra cqlsh -e "SELECT * FROM university.student_courses WHERE student_id='s1';"
docker compose exec neo4j cypher-shell -u neo4j -p lab16password "MATCH (s:Student)-[:ENROLLED_IN]->(c:Course) RETURN s.name, c.title"
```

## Docker Hub publish (after verifying)
```bash
docker login
docker build --platform linux/amd64 -t rayhann094/lab16-polyglot:latest .
docker push rayhann094/lab16-polyglot:latest
```
**Important:** `docker push` publishes only the Python application image, **not** the three database images, Compose stack, volumes, or data. A grader needs `compose.yaml` and the code to reproduce the demonstration. Give them the ZIP or a repository with `compose.yaml`, or publish a Docker Hub repository description that links to those setup files. Do not claim a standalone image runs all 3 databases.

## Optional shutdown
`docker compose down` stops Lab 16 without deleting its volumes. **Never use `down -v` unless you intend to delete the seeded data.**

## Files
- `scripts/seed.py` seeds student/course enrollment, fraud transactions, time-series records, prerequisite edges, and a fraud ring.
- `scripts/lab16_1.py` runs 3 comparable queries in all 3 databases plus a Neo4j prerequisites query.
- `app/fraud_service.py` implements FraudQueryService, backend pools and circuit breakers.
- `scripts/lab16_2.py` is the real-database integration demonstration.
- `tests/test_fraud_service.py` has six mock-based unit tests.
- `docs/schema_and_comparison.md` covers schema design, comparison, hybrid architecture, and limitations.

## Security note
Demo credentials and default Neo4j password are for local lab work only, not public deployments. Run the services only on localhost / private Docker network.
