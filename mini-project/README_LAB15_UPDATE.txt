CTI Sentinel — Lab 15-only Live SaaS Update

1. Stop the CTI Sentinel server (Control+C). Keep Docker running.
2. cd ~/Downloads
3. unzip -o CTI_Sentinel_Lab15_Only_Update.zip
4. cd ~/Downloads/NoSQL_Sentinel_18_Labs
5. bash start_sentinel.command
6. Open http://127.0.0.1:8765/sentinel?lab=15 then Command+Shift+R in Brave.

Only Lab 15 UI and /api/sentinel/lab15/* endpoints have been added.
The patch includes cumulative server.py and sentinel.js so Labs 11–14 remain available.
It uses a dedicated lab15_saas_live_demo MongoDB database on rsLab10 localhost:27022.
Seeding and migration are idempotent. No deletes, drops or cross-database writes.
Tenant switching in UI is illustrative — NOT secure authenticated tenant isolation.
Rate-limit counters use a TTL index; expiry is asynchronous.
For actual JWT/RBAC and production rate limiting, use your separately deployed Lab15 TaskTracker application.
