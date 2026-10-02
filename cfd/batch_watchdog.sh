#!/bin/bash
# Overnight watchdog: monitors AERO batch, auto-resumes on crash, logs to database/monitor.log
# Run detached: nohup bash cfd/batch_watchdog.sh </dev/null >/dev/null 2>&1 & disown
UAUV=/Users/ianzhang/UAUV
LOG=$UAUV/cfd/database/monitor.log
CSV=$UAUV/cfd/database/aero_results.csv
BATCH=$UAUV/cfd/batch_aero.sh

log() { echo "$(date '+%H:%M:%S')  $1" | tee -a "$LOG"; }

log "WATCHDOG STARTED. Monitoring $CSV"
LAST_ROWS=0
STALL_COUNT=0
while true; do
    # Count completed rows
    ROWS=$(grep -cE "^Wing" "$CSV" 2>/dev/null || echo 0)
    RUNNING=$(pgrep -c batch_aero 2>/dev/null || echo 0)
    SOLVING=$(pgrep -c simpleFoam 2>/dev/null || echo 0)

    if [ "$ROWS" -gt "$LAST_ROWS" ]; then
        STALL_COUNT=0
        LAST_ROW=$(tail -1 "$CSV" 2>/dev/null)
        log "[$ROWS rows] $LAST_ROW"
    elif [ "$RUNNING" -eq 0 ]; then
        log "!! BATCH DIED at $ROWS rows. Attempting restart..."
        nohup openfoam bash -c "bash $BATCH 2>&1 | tee $UAUV/cfd/database/aero_batch.log" </dev/null >/dev/null 2>&1 &
        disown
        log "  relaunched (PID $(pgrep -f batch_aero | head -1))"
        STALL_COUNT=0
    elif [ "$SOLVING" -gt 0 ]; then
        STALL_COUNT=0
    else
        # Batch running but no solver — might be meshing or between runs
        STALL_COUNT=$((STALL_COUNT+1))
        if [ "$STALL_COUNT" -gt 60 ]; then  # 5 min stall
            log "!! STALLED 5min. Killing and restarting..."
            pkill -9 -f batch_aero 2>/dev/null; pkill -9 -f simpleFoam 2>/dev/null
            sleep 5
            nohup openfoam bash -c "bash $BATCH 2>&1 | tee $UAUV/cfd/database/aero_batch.log" </dev/null >/dev/null 2>&1 &
            disown
            STALL_COUNT=0
        fi
    fi
    LAST_ROWS=$ROWS
    sleep 15
done
