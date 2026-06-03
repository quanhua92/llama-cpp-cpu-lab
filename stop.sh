#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8080}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$SCRIPT_DIR/server.${PORT}.pid"

if [ ! -f "$PIDFILE" ]; then
    echo "No PID file found for port $PORT at $PIDFILE"
    exit 1
fi

PID=$(cat "$PIDFILE")
echo "Stopping llama-server on port $PORT (PID $PID)..."
kill "$PID" 2>/dev/null && echo "Stopped." || echo "Process not running."
rm -f "$PIDFILE"
