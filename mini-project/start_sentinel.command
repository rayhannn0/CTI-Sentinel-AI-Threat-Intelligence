#!/bin/bash
set -e
cd "$(dirname "$0")"
# Dedicated Lab 10 replica-set connection for ACID transactions.
# Historical Lab 18 threat records remain on the original MongoDB instance.
export LAB18_MONGO_URI="${LAB18_MONGO_URI:-mongodb://127.0.0.1:27022/?replicaSet=rsLab10}"
export LAB18_THREAT_URI="${LAB18_THREAT_URI:-mongodb://127.0.0.1:27021}"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -q -r requirements.txt
printf '\nOPEN CTI SENTINEL: http://127.0.0.1:8765/sentinel\nBank replica set: %s\nThreat records: %s\nKeep this Terminal open. Press Ctrl+C to stop.\n\n' "$LAB18_MONGO_URI" "$LAB18_THREAT_URI"
.venv/bin/python server.py
