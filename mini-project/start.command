#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
printf '\n\nWebsite: http://127.0.0.1:8765\nKeep this Terminal window open. Press Ctrl+C to stop.\n\n'
.venv/bin/python server.py
