#!/bin/bash
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"

for f in dashboard orchestrator; do
  PID_FILE="$LOG_DIR/$f.pid"
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null && echo "Stopped $f (PID $PID)"
    rm "$PID_FILE"
  fi
done
echo "All services stopped."
