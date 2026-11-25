# Lab 11 — MongoDB Shard Key Selection and Hotspot Detection

This project creates a **real two-shard cluster** (MongoDB 7.0), a config-server replica set and mongos router. Each shard is a one-node replica set; this is for local demonstrations, not production HA.

## macOS quick start (Docker Desktop running)

1. Extract ZIP under `~/Downloads/lab11/Lab11_MongoDB_Docker` (or navigate to your actual extracted folder).
2. `cd ~/Downloads/lab11/Lab11_MongoDB_Docker`
3. `python3 bootstrap.py` — initializes config server and both shards, then mongos.
4. `docker compose --profile runner build labrunner`
5. `docker compose --profile runner run --rm labrunner`
6. Compass: `mongodb://127.0.0.1:27517/?directConnection=true` — database `lab11`.
7. `python3 -m pip install -r requirements.txt`
8. `python3 generate_report.py`
9. `docker login`
10. `docker tag lab11-mongodb-assessment:latest rayhann094/lab11-mongodb-assessment:latest`
11. `docker push rayhann094/lab11-mongodb-assessment:latest`
12. `printf '%s\n' 'https://hub.docker.com/r/rayhann094/lab11-mongodb-assessment' > docker_hub_url.txt`
13. `python3 make_submission_pdf.py`
14. Open `Lab11_DockerHub_Submission.pdf`, verify repository link and accessibility, then submit.

`output/` contains four actual run result JSON files after execution. The benchmark resets `lab11.hotspot_data` and `lab11.even_data` on each run. The results are environment-dependent: the example 9500/500 and 5000/5000 splits are NOT guaranteed. A monotonically increasing key can route all inserts to one shard initially. `collStats` gives observed per-shard counts. Range queries on a hashed key generally scatter.

**Demonstration:** Docker Hub image is a Python runner, NOT the whole database cluster. Keep the Compose file and run bootstrap first. Do not use `docker compose down -v` unless you intend to erase all lab11 data.
