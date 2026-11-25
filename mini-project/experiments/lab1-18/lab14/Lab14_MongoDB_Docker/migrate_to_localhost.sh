#!/bin/bash
set -euo pipefail
FILE="$HOME/Downloads/MongoDB_Lab_Backups/lab14.archive"
mkdir -p "$(dirname "$FILE")"
echo "Exporting lab14 from Docker MongoDB port 27817..."
mongodump --uri="mongodb://127.0.0.1:27817/" --db=lab14 --archive="$FILE"
echo "Restoring lab14 into your main MongoDB port 27017..."
mongorestore --uri="mongodb://127.0.0.1:27017/" --archive="$FILE" --nsInclude="lab14.*"
echo "Done. Refresh Compass at localhost:27017."
