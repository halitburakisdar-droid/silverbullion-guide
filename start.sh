#!/bin/bash
# SilverBullion.guide - Start all services
# Usage: ./start.sh

BLOG_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$BLOG_DIR/logs"
mkdir -p "$LOG_DIR"

echo "Starting SilverBullion.guide services..."

# Dashboard
python3 "$BLOG_DIR/dashboard/app.py" > "$LOG_DIR/dashboard.log" 2>&1 &
DASH_PID=$!
echo "  Dashboard PID=$DASH_PID → http://localhost:8888"

# Orchestrator
python3 "$BLOG_DIR/agent/orchestrator.py" > "$LOG_DIR/orchestrator.log" 2>&1 &
ORCH_PID=$!
echo "  Orchestrator PID=$ORCH_PID"

echo "$DASH_PID" > "$LOG_DIR/dashboard.pid"
echo "$ORCH_PID" > "$LOG_DIR/orchestrator.pid"

echo ""
echo "All services running."
echo "Dashboard: http://localhost:8888"
echo "Stop with: ./stop.sh"
