# Lab 7 — Corrected Cyber Threat Intelligence Project

MongoDB Compass **database name: `lab7`**. Includes frontend + backend and all 4 Lab 7 assignments. **Threat records are synthetic educational examples, not a CTI Digest database export, nor real verified alerts.** Annual report discovery imports link metadata only.

## MacBook installation

1. Install/start **MongoDB Community Server** (Compass is only the GUI). Connect Compass to `mongodb://127.0.0.1:27017/`.
2. Open Terminal inside this extracted folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 verify_project.py
python3 connection.py
python3 run_all.py
python3 -m backend.app
```

3. Open `http://127.0.0.1:5000` for the web interface. Refresh Compass to view `lab7`.

### Individual activities

```bash
python3 lab_7_1/lab_7_1.py
python3 activity_7_1/activity_7_1.py
python3 lab_7_2/lab_7_2.py
python3 activity_7_2/activity_7_2.py --cycles 3
```

**Important:** The Lab 7.2 benchmark intentionally **drops/replaces only `lab7.working_set`**, generating 100,000 records of roughly 2 KB (about 200 MB plus overhead). The 10-second monitor can run forever when invoked without `--cycles`; use `--once` for one sample. By default it fetches GitHub report link metadata once per minute; use `--no-discovery` to monitor offline.

## Collections

`threats`, `sources`, `reports`, `threats_embedded`, and after the benchmark `working_set`. The core `run_all.py` is idempotent with respect to seeded source records and does not delete the original threat documents.

## Fixes compared with first ZIP

- API returns a useful **400 error** for invalid `page`/`limit` instead of raising an uncaught `ValueError`.
- Source embedding now uses `$lookup` + `$merge` without deleting the derived collection before writing, and never classifies a source as factual threat evidence.
- Working-set counters handle unavailable WiredTiger metrics, and clearly label the cache **hit proxy** as an estimate instead of a true hit percentage.
- Report monitor has `--once`, `--cycles`, and `--no-discovery` controls to make it easier to test.
- Each standalone lab script imports shared connection from the project root; `verify_project.py` checks syntax and JSON.
- All runnable programs target the `lab7` database by default; no schema validator uses `exclusiveMinimum`.

## When MongoDB does not connect

`ServerSelectionTimeoutError` means the local server may not be running, the port is wrong, or authentication is required. Set `MONGODB_URI` to your own server URI. Compass successfully opening does not by itself mean Python is using the same URI.

`serverStatus unauthorized` means you need an account with monitoring permission. The frontend and Lab 7.1 still work without that command.

## References

- https://ctidigest.com/
- https://github.com/jacobdjwilson/awesome-annual-security-reports
- https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-07
