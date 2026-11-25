# Lab 18 - Threat Intelligence False-Positive Comparison

**Important:** This Docker project uses **100,000 reproducible SYNTHETIC records**, not a live threat feed. The generated confidence/false-positive fields are teaching heuristics, not verified security evidence. Nothing scans external systems.

## Contents
- **Lab 18.1** MongoDB document store, Cassandra query-driven tables, Neo4j graph; 4 benchmark patterns in **each of 3 stores**, **10 runs each**; median latency in output/benchmark.csv/json
- **Try it yourself:** Neo4j SUSPICIOUS graph edges, connected-components heuristic, and MongoDB investigation cross-reference, output/communities.json
- **Lab 18.2:** comparative PDF report generator with **actual measured latencies**, modeling, ergonomics, scaling estimates, and recommendations
- 6 offline unit tests, README, Docker Compose, PDF submission template

## macOS: commands in extracted project directory
```bash
cd ~/Downloads/lab18/Lab18_Threat_Intelligence_Docker_Submission  # only if extracted here
ls
# If path differs: find ~/Downloads -iname compose.yaml -ipath '*lab18*' -print
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec app python -m pytest -q
# Smoke test first:
docker compose exec app python -m scripts.seed --count 1000
docker compose exec app python -m scripts.benchmark
docker compose exec app python -m scripts.communities
docker compose exec app python -m scripts.report
# Full assessment, replace smoke dataset with required 100k records:
docker compose exec app python -m scripts.seed --count 100000
docker compose exec app python -m scripts.benchmark
docker compose exec app python -m scripts.communities
docker compose exec app python -m scripts.report
```

The 100k seed writes to all databases and is **resource intensive**, especially Cassandra and Neo4j; on MacBook Docker Desktop allocate >= 8 GB memory if feasible, close other lab stacks via their own compose directory, and expect nontrivial runtime. The seed is idempotent for the base 100k threat IDs; seeded MongoDB summaries are rebuilt from the requested count. Benchmark inserts 100 additional events per backend and retains those rows. **Do not submit smoke-run latency or counts as full 100k-run results.** If you run the 1k smoke before the 100k seed, re-run benchmark only after full seed.

## Services / ports
- MongoDB: host localhost:27021 -> container mongo:27017 (MongoDB Compass `mongodb://localhost:27021`)
- Neo4j Browser: http://localhost:7476, user neo4j, password lab18securepassword (local lab credential only)
- Cassandra: internal container network, app uses `cassandra:9042`
- Python app: no exposed port, runs commands via `docker compose exec app ...`
- Docker only; never use localhost:27017 inside an app container.

## Query design
**History:** 50 latest threats for source `sensor-01` (Mongo compound index, Cassandra source partition, Neo4j REPORTED traversal).
**Target/spread:** threat records for target `host-001` (Mongo target index, Cassandra target partition, Neo4j target property).
**Daily volume:** aggregate by source for day `2026-11-20` (Mongo/Neo4j live aggregation; Cassandra **precomputed daily_volume** - cannot interpret as like-for-like query latency).
**Insert throughput:** 10 events inserted per timed sample x10; Cassandra writes 3 separate denormalized tables, Mongo one collection, Neo4j creates node+relationship. Thus measure pattern-specific pipeline throughput, not equivalent payload writes.

## False-positive limitations
The `SUSPICIOUS` edges indicate shared fingerprints, NOT proven collusion. `is_false_positive` is a synthetic confidence threshold. Connected components do not calculate statistically significant anomalous density; they are a practical graph-based candidate detector. Graph algorithm uses source connections and cross-references raw Mongo event samples. For research-grade false-positive metrics, use labeled ground truth, confusion matrix, precision/recall/F1 and calibrated thresholds.

## Report / deliverables
`output/Lab18_Comparative_Report.pdf` is generated after benchmark, and contains measured numbers and caveats. The included root PDF is a **template**, not a report claiming measurements. `output/benchmark.csv`, `output/benchmark.json`, `output/communities.json` are saved on the Mac via bind mount.

After successful local tests and full dataset run:
```bash
docker build --platform linux/amd64 -t rayhann094/lab18-threat-intelligence:latest .
docker push rayhann094/lab18-threat-intelligence:latest
```
Docker Hub URL: `https://hub.docker.com/r/rayhann094/lab18-threat-intelligence` (exists only after confirmed push). Uploaded image is Python app; evaluator also needs **compose.yaml** for MongoDB/Cassandra/Neo4j and `seed` command to reproduce results. Consider publishing compose.yaml and README in your submission alongside the PDF; the image alone is not a complete 4-service demo.

## Sources / scaling context
- https://www.mongodb.com/docs/manual/sharding/
- https://neo4j.com/docs/operations-manual/current/scalability/scaling-with-neo4j/
- https://cassandra.apache.org/doc/latest/cassandra/managing/operating/
