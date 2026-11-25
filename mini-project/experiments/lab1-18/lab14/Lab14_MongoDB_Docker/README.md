# Lab 14 - MongoDB Monitoring and Backup/Restore Verification

This Docker project implements Lab 14.1 and Lab 14.2 using the Chapter 14 reference scripts as a base, with the assignment's 30-second monitoring interval, <80% cache-hit warning, >10-second replication-lag warning, webhook extension, hourly backups, seven-day retention, and 1k/10k/100k restore benchmarks.

## Files
- `monitoring_dashboard.py`: serverStatus metrics, rich table, log file, threshold alerts, optional Slack/Discord webhook.
- `backup_restore.py`: timestamped mongodump, restore with `--drop` restricted to `lab14.backup_test`, count + checksum verification, and benchmarks.
- `backup_scheduler.py`: initial backup then hourly backups; deletes backup folders older than seven days.
- `run_all.py`: one monitoring snapshot plus Lab 14.2 benchmark suite.
- `migrate_to_localhost.sh`: copies `lab14` from Docker port 27817 to host MongoDB port 27017.

## 1. Start MongoDB and build the runner
```bash
docker compose up -d mongo
docker compose --profile runner build labrunner
```
The Docker MongoDB is exposed at `127.0.0.1:27817`, so it does not replace your existing `localhost:27017` or conflict with Labs 12/13.

## 2. Run both activities
```bash
docker compose --profile runner run --rm labrunner
```
Generated evidence: `logs/metrics.log`, `backups/` timestamped folders, and `output/backup_benchmark.csv`. The destructive restore test touches only `lab14.backup_test`.

## 3. Run monitoring every 30 seconds
```bash
docker compose --profile runner run --rm labrunner python monitoring_dashboard.py
```
Press Ctrl+C to stop. One snapshot: add `--once`. The WiredTiger cache hit ratio is estimated from page counters: `(pages requested from cache - pages read into cache) / pages requested from cache`. A standalone server reports replica-set lag as not applicable.

## 4. Optional webhook alerts
Copy `.env.example` to `.env`, put your own incoming Slack/Discord webhook URL in `WEBHOOK_URL`, then run the monitoring command. Keep `.env` private.

## 5. Enable hourly backup service and seven-day retention
```bash
docker compose --profile scheduler up -d backup-scheduler
docker compose logs -f backup-scheduler
```
Stop with `docker compose --profile scheduler stop backup-scheduler`.

## 6. View in Compass
Connect to `mongodb://127.0.0.1:27817/` and inspect `lab14.backup_test`.

## 7. Copy lab14 into your main localhost:27017
Make sure the main MongoDB server is running on port 27017, then:
```bash
chmod +x migrate_to_localhost.sh
./migrate_to_localhost.sh
```
Refresh the existing Compass `localhost:27017` connection. This copies database contents only, not Docker configuration. It does not drop existing databases.

## 8. Docker Hub and submission PDF
```bash
docker login
docker tag lab14-mongodb-assessment:latest YOUR_DOCKERHUB_USERNAME/lab14-mongodb-assessment:latest
docker push YOUR_DOCKERHUB_USERNAME/lab14-mongodb-assessment:latest
python3 make_submission_pdf.py --docker-url https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/lab14-mongodb-assessment
```
Replace the placeholder with your actual Docker Hub username. Keep this project folder and Compose file with the image for demonstration.

## Safety
Do not run restore verification against a production collection. The lab intentionally changes and restores only the dedicated `lab14.backup_test` collection. Keep webhook URLs and `.env` private.
