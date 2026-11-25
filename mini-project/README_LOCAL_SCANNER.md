# CTI Sentinel — Opt-in read-only macOS scanner

## Changes in this update
- New `local_scanner.py` FastAPI router. Existing labs, their data, and existing chat routes are unchanged.
- `Scan My Mac` UI in `/advisor`, requiring explicit consent before each scan.
- Checks macOS version, Gatekeeper status, FileVault status, automatic update schedule, launch agent/daemon file counts, and TCP listener count. These are limited observations, **not malware scans, CVE detection, or confirmation of compromise**.
- Results saved to `cti_advisor.local_scans` in the existing MongoDB service. Session-scoped recent scan history displayed in the dashboard.
- Separate consent for `Ask Gemini to assess scan`, which transmits only the limited observation summary (no process command lines, file paths, IPs, or secrets) to Gemini. Gemini suggestions are advisory only; the tool performs no fixes.
- The Gemini startup script now uses the installed `certifi` trust bundle when available and defaults to `gemini-3.5-flash-lite`. It never embeds an API key.

## Install (MacBook)
1. Quit the old CTI Sentinel Python server with Control+C in the Terminal running it. If a launch agent restarts it, stop that first. **Check `lsof -nP -iTCP:8765 -sTCP:LISTEN` is empty before starting.** Do not kill an unrelated process.
2. Back up your existing project folder. Extract this ZIP into `~/Downloads`, replacing/updating the project source files. No MongoDB data is included or overwritten.
3. `cd ~/Downloads/NoSQL_Sentinel_18_Labs`
4. `.venv/bin/python -m pip install -r requirements.txt` (if not already installed)
5. `.venv/bin/python -m pip install certifi` (if needed for Python HTTPS trust)
6. `bash start_with_gemini.command` and paste your valid Gemini API key when prompted. Keep this Terminal open.
7. Open `http://127.0.0.1:8765/advisor` and select `Scan My Mac` after reading the consent text. Select the **separate** Gemini checkbox if you want AI interpretation.

## Design and boundaries
- The scanner only runs when the Python server is running natively on **macOS**, and only accepts requests from a loopback client. Running the backend in Docker/Linux cannot scan the Mac host.
- Fixed allowlisted read-only commands use `subprocess.run` without a shell or elevated permissions. No uploads, deletion, killing, patching, network isolation, or automatic remediation.
- The displayed risk statuses are basic configuration observations (`pass`, `review`, `info`, `unknown`), not threat detections. Unknown and pass are not safety guarantees.
- No background monitoring is installed. Each scan is explicitly user initiated.
- Local scan summaries persist in MongoDB; consider retention/access controls before using with real devices. The database and local web app are a **development demo** and are not hardened for multi-user or production deployment.
- The AI analysis depends on model availability, valid key, and quota. 503 responses may still occur.

## API
- `POST /api/advisor/local-scan`: JSON `{ "session_id": "demo", "confirmation": "RUN_READ_ONLY_MACOS_SCAN" }`
- `GET /api/advisor/local-scans?session_id=demo`
- `POST /api/advisor/analyze-local-scan`: JSON `{ "session_id": "demo", "scan_id": "<returned uuid>", "confirmation": "SEND_SUMMARY_TO_GEMINI" }`

This lab demonstration does not independently verify current vulnerability advisories or verify that any executable is malware. Use a trusted endpoint security scanner and incident responder for authoritative threat detection.
