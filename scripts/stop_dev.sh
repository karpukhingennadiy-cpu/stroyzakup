#!/bin/bash
# Остановка dev-процессов, запущенных через start_dev.sh.
set -uo pipefail

PIDS_FILE=/tmp/stroyzakup_dev.pids

if [ ! -f "$PIDS_FILE" ]; then
    echo "No PID file at $PIDS_FILE — nothing to stop."
    exit 0
fi

echo "=== Stroyzakup dev stopper ==="
while IFS= read -r pid; do
    [ -z "$pid" ] && continue
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null && echo "Killed PID $pid"
    else
        echo "PID $pid already gone"
    fi
done < "$PIDS_FILE"

rm -f "$PIDS_FILE"
echo "Removed $PIDS_FILE"
echo "Done."