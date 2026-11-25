# Lab 8 — Replica Sets & Elections (corrected submission)

**Use Mac Terminal, NOT the MongoDB `mongosh` prompt, for `cd` and `python3`.**

This version uses a dedicated Docker Compose project **`lab8_stable_submission`**, containers `lab8stable-mongo1` / `lab8stable-mongo2` / `lab8stable-mongo3` / `lab8stable-arbiter`, and local ports **27217–27220**. It does **not** stop or delete containers and volumes from previous Lab 8 ZIP versions. Port numbers are intentionally different to prevent collisions with old containers on 27117–27120.

## 1. Setup (after unzipping)

Open Docker Desktop. In Terminal, change into the directory containing `run_all.py` (e.g. `cd ~/Downloads/lab8/Lab8_Complete_Error_Fixed`).

```bash
python3 -m pip install -r requirements.txt
python3 verify_project.py
python3 check_docker.py
python3 bootstrap.py
```

## 2. Run all activities with safe ordering

```bash
python3 run_all.py
python3 generate_report.py
```

`run_all.py` bootstraps the set, restores its original three voting data nodes if an arbiter was added on a previous run, and then runs 8.1, 8.2, Try It Yourself 8.2, and **Try It Yourself 8.1 last**. Each actual activity result goes to `output/*.txt`; generating the DOCX uses these logs. If a step fails, the runner stops and prints the error.

To run Try It Yourself 8.2 *after* Try It Yourself 8.1, first run `python3 restore_baseline.py` and confirm `python3 connection.py` shows NO arbiter. The restore script changes **only one voting member at a time** and does not use `force`.

## 3. MongoDB Compass

Connect to: `mongodb://127.0.0.1:27217/?directConnection=true` (or 27218 / 27219). Database: **lab8**, collection: `replication_demo` after Lab 8.1 writes a document. Refresh Compass. This is a direct connection to one node, not a topology-discovering host-side replica set URI; member DNS names such as `mongo1` are internal to Docker.

## 4. Live failover monitoring

In one Terminal run `python3 03_Lab_8_2/monitor_failover.py`; in another Terminal run `python3 03_Lab_8_2/lab_8_2.py`. Ctrl+C stops the monitor. Capture actual screenshots if required by your instructor.

## 5. Submission files

Four activity directories each contain the Python activity and representative MongoDB JSON output/schema file. `Lab8_Report.docx` includes all scripts and output-image sections. **Before running**, screenshots are marked *illustrative*, not actual database proof. After running `run_all.py`, `generate_report.py` regenerates screenshots from saved real terminal outputs. For strict screenshot requirements, also capture your Terminal/Compass screenshots yourself.

## 6. Errors addressed

- Missing `docker`: Docker CLI auto-discovered with `docker_utils.py`; `check_docker.py` checks engine.
- Wrong directory: run commands only after `cd` into this project folder.
- Container name conflicts: dedicated container names and stable Compose project.
- Reconfig error 103: arbiter is removed, then a data node voter restored, in **separate** changes.
- Arbiter already present: runner restores baseline before election-priority activity.
- Missing database in Compass: `lab8` appears after successful Lab 8.1 write, through port 27217.

**Never run `docker compose down -v` unless you intentionally want to erase this lab's MongoDB volumes.** This lab deliberately disables authentication for local Docker demonstration only; don't expose these ports beyond localhost.

Reference: https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-08

## Priority-election test correction

The earlier Try It Yourself 8.2 predicted `mongo1` but `mongo3` became PRIMARY. This is possible: **priority alone does not guarantee the immediate election winner**. The corrected `activity_8_2.py` temporarily assigns priority 5 to the selected healthy secondary, priority 0 to the other secondary, and priority 1 to the current primary, then verifies the *actual* elected node. A priority takeover can happen before the explicit `stepDown`; the output distinguishes that case. Original priorities are restored at the end. Do not edit screenshots or report a correct prediction unless the live output confirms it. Re-run `python3 run_all.py`, then `python3 generate_report.py` to update the report with newly recorded terminal output.
