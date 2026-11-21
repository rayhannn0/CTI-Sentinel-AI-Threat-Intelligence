#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -z "${GEMINI_API_KEY:-}" ]; then
  printf "Paste your Gemini API key (input hidden): "
  IFS= read -r -s GEMINI_API_KEY
  printf "\n"
fi
if [ -z "$GEMINI_API_KEY" ]; then
  echo "No API key supplied. Nothing started."; exit 1
fi
export GEMINI_API_KEY
export GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
exec bash start_sentinel.command
