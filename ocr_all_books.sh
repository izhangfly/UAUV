#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Overnight full-book OCR for the UAUV reference library.
# Resumable (skips files already done), memory-light, keeps the Mac awake.
#
# RUN IT (in Terminal, before bed):
#     cd ~/UAUV && caffeinate -i bash ocr_all_books.sh
#
#   caffeinate -i  = stop the Mac idle-sleeping mid-run (display may still sleep).
#   Progress + errors stream to refs/ocr/ocr_run.log ; each book -> refs/ocr/<name>.mmd
#   If it crashes or you stop it, just run the same command again — it resumes.
# ---------------------------------------------------------------------------
set -u
V=/Users/ianzhang/UAUV/.venv-nougat/bin
REFS=/Users/ianzhang/UAUV/refs
OUT=$REFS/ocr
LOG=$OUT/ocr_run.log
MODEL=0.1.0-small     # small = lower RAM + ~2x faster. For max equation accuracy use 0.1.0-base.

mkdir -p "$OUT"
echo "=================== OCR run started $(date) (model=$MODEL) ===================" | tee -a "$LOG"
shopt -s nullglob
count=0
for pdf in "$REFS"/*.pdf; do
    base=$(basename "$pdf" .pdf)
    if [ -f "$OUT/$base.mmd" ]; then
        echo "SKIP (already done): $base" | tee -a "$LOG"
        continue
    fi
    count=$((count+1))
    echo ">>> [$count] OCR START: $base   $(date)" | tee -a "$LOG"
    if "$V/nougat" "$pdf" -o "$OUT" -m "$MODEL" --batchsize 1 >>"$LOG" 2>&1; then
        echo "    OK: $base" | tee -a "$LOG"
    else
        echo "    FAIL: $base  (see $LOG)" | tee -a "$LOG"
    fi
done
echo ">>> building viewable HTML (math-rendered)..." | tee -a "$LOG"
python3 /Users/ianzhang/UAUV/view_ocr.py >>"$LOG" 2>&1 || echo "  (view_ocr.py failed, see log)" | tee -a "$LOG"
echo "=================== OCR run finished $(date) — $count new file(s) ===================" | tee -a "$LOG"
echo "View results: open ~/UAUV/refs/ocr/html/index.html"
