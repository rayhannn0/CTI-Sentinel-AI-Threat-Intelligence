# CTI Sentinel — user-approved reversible file quarantine

This add-on **does not automatically detect or clear malware**. The limited macOS scanner checks configuration signals, which are insufficient for deciding that a process or file is malicious. Gemini can explain scan findings but cannot run remediation commands.

For a *separately identified* suspicious regular file directly inside the logged-in user's `~/Downloads` directory, the user can:

1. Enter the exact filename (not a path) and preview its SHA-256.
2. Review the fingerprint and explicitly approve quarantine in the dashboard, including the final confirmation dialog.
3. Move only that same file into `~/.cti_sentinel_quarantine/` (private permissions); a record is written to MongoDB.
4. Restore it later using Quarantine history; existing Downloads files are never overwritten.

Limits: maximum 100 MiB; no directories, hidden files, links, or system files; the process runs as the logged-in user without sudo. No files are scanned for malicious signatures. This is not comprehensive antivirus protection, removal of infections or threat intelligence validation. FileVault and LaunchAgent observations are not proof of malware and do not trigger quarantine. Quarantine may interrupt applications if the user selected a file they need. Back up important data before quarantine. The quarantine directory is not a hardened sandbox; don't execute quarantined files or treat them as safe.

The application still uses a loopback-only API. No automatic threat remediation runs in the background. Each apply/restore operation requires a deliberate action. Scan summaries are sent to Gemini only after separate consent.

## Startup

Stop the existing server on port 8765. Then:

```bash
cd ~/Downloads/NoSQL_Sentinel_18_Labs
export SSL_CERT_FILE="$(.venv/bin/python -m certifi)"
GEMINI_MODEL=gemini-3.5-flash-lite bash start_with_gemini.command
```

Visit http://127.0.0.1:8765/advisor and find **Controlled File Quarantine** below Mac Security Check. Only use this feature on a file that you independently chose to quarantine.
