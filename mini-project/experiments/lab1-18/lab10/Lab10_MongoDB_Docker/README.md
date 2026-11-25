# MongoDB Lab 10 — Docker transaction assessment

Four working exercises, one Dockerized Python runner, and a three-node MongoDB 7.0 replica set. This project is independent of Lab 9 and uses database **lab10** and Mac host port **27417**.

## Requirements
- Docker Desktop running on your Mac.
- Python 3 installed for the host bootstrap script (`bootstrap.py` only requires the standard library).
- `python3 -m pip install -r requirements.txt` for report/PDF generation on Mac.

## Exactly what to type on your Mac

Unzip `Lab10_MongoDB_Docker.zip` into Downloads. Open Terminal and type:

```bash
cd ~/Downloads/Lab10_MongoDB_Docker
python3 bootstrap.py
docker compose --profile runner build labrunner
docker compose --profile runner run --rm labrunner
python3 verify_project.py
python3 generate_report.py
```

**Do not run the activity Python scripts directly on your Mac**: the default MongoDB URI uses Docker-only hostnames `mongo1`, `mongo2`, and `mongo3`. The Docker runner can reach the replica set. All results and BSON-to-JSON exports are stored in the project's `output/` folder, which is mounted into the runner. You can also run one activity at a time:

```bash
docker compose --profile runner run --rm labrunner python 01_Lab_10_1/lab_10_1.py
docker compose --profile runner run --rm labrunner python 02_Activity_10_1_Try_It_Yourself/activity_10_1.py
docker compose --profile runner run --rm labrunner python 03_Lab_10_2/lab_10_2.py
docker compose --profile runner run --rm labrunner python 04_Activity_10_2_Try_It_Yourself/activity_10_2.py
```

**Note:** The four scripts intentionally reset their respective collections for reproducibility. Run all four together in order to produce the final Compass collections and activity exports.

## MongoDB Compass connection

1. Open MongoDB Compass.
2. Add New Connection.
3. Paste `mongodb://127.0.0.1:27417/?directConnection=true`.
4. Save as `Lab 10 - MongoDB Docker`; connect and refresh.
5. Expand database `lab10`. Collections include `accounts`, `transfer_history`, `inventory`, and `orders`.

`directConnection=true` is for connecting Compass directly to the published `mongo1` port. The application runner connects to all three internal replica-set members on the Compose network.

## Deliverable mapping

| Activity | Script | Actual JSON result | Actual collection export |
|---|---|---|---|
| Lab 10.1 | `01_Lab_10_1/lab_10_1.py` | `output/lab_10_1.json` | `output/lab_10_1_export.json` |
| Activity 10.1 | `02_Activity_10_1_Try_It_Yourself/activity_10_1.py` | `output/activity_10_1.json` | `output/activity_10_1_export.json` |
| Lab 10.2 | `03_Lab_10_2/lab_10_2.py` | `output/lab_10_2.json` | `output/lab_10_2_export.json` |
| Activity 10.2 | `04_Activity_10_2_Try_It_Yourself/activity_10_2.py` | `output/activity_10_2.json` | `output/activity_10_2_export.json` |

Lab 10.1 validates success, insufficient-funds rollback, and no spurious history. Activity 10.1 demonstrates retry of labeled transient errors, explicitly simulated twice to make backoff reproducible, then executes a real transaction. Lab 10.2 uses 8 concurrent requests with stock 5 and verifies 5 succeed/3 fail. Activity 10.2 benchmarks 1/4/8/16 workers with measured values; the final test deliberately injects an order-insertion failure after **nontransactional** stock decrement to demonstrate inconsistency. Results depend on your machine.

## Docker Hub submission (after successful local demonstration)

1. Verify `docker login` has succeeded.
2. Tag the built application image using **your own** Docker Hub username:

```bash
docker tag lab10-mongodb-assessment:latest YOUR_USERNAME/lab10-mongodb-assessment:latest
docker push YOUR_USERNAME/lab10-mongodb-assessment:latest
```

3. Edit `docker_hub_url.txt` to contain one plain URL line, like `https://hub.docker.com/r/YOUR_USERNAME/lab10-mongodb-assessment` (no brackets/Markdown).
4. `python3 make_submission_pdf.py`
5. Submit `Lab10_DockerHub_Submission.pdf` and make the **Compose project** available for demonstration. The Docker Hub image alone runs the assessment runner but does not contain MongoDB server containers; evaluators need the supplied Compose file for the three-server replica set.

The project uses `LAB10_IMAGE` in Compose if the demonstrator wants to run the published image instead of the locally built one:

```bash
LAB10_IMAGE=YOUR_USERNAME/lab10-mongodb-assessment:latest docker compose --profile runner run --rm --no-build labrunner
```

## Notes
- Do not run `docker compose down -v` unless you want to destroy the database data.
- This is a demonstration environment with **no database authentication**; do not expose the database to public networks.
- A PNG evidence image in the Word report is a rendering of **actual saved JSON**, not a fabricated Terminal screenshot. Take a real Terminal screenshot for strict grading if necessary.
- This implementation is based on the lab specifications in the assignment text. The linked GitHub Chapter 10 source could not be fetched automatically during packaging; exact source-code correspondence has not been verified.
