CTI Sentinel — Lab 14 monitoring & backup interface only

Install from Downloads:
  unzip -o CTI_Sentinel_Lab14_Only_Update.zip
  cd ~/Downloads/NoSQL_Sentinel_18_Labs
  bash start_sentinel.command

Stop the existing server (Ctrl+C) before restarting. Keep MongoDB Docker containers running.
Open http://127.0.0.1:8765/sentinel?lab=14 and hard-refresh in Brave (Cmd+Shift+R).

LAB 14.1:
- Live MongoDB serverStatus active/available connections.
- WiredTiger cumulative page-counter derived cache proxy, NOT a true measured cache hit rate.
- User-set threshold compared to the clearly labeled proxy; on-page alert only, no webhook.
- Background comparison table for backup RPO/RTO, labeled reference estimates only.

LAB 14.2:
- Creates a JSON snapshot of only lab14_monitoring_demo.backup_test_records (synthetic, demo-only).
- Verifies that the latest JSON snapshot parses and that the SHA-256 can be calculated.
- Does NOT perform mongodump/mongorestore, run scheduled backups, or guarantee disaster recovery.
- Original lab experiment actions remain below the new dashboard.

Important: This package contains merged Lab 11, Lab 12, and Lab 13 code from the previous patches.
No database volumes are removed or modified. Only Lab14's dedicated demo collection is seeded.
