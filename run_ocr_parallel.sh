#!/usr/bin/env bash
# Memory-SAFE OCR: each book is PHYSICALLY split into small sub-PDFs on disk, so nougat
# only ever opens a tiny file (nougat loads the whole input PDF into RAM, so page-range
# flags do NOT bound memory -- physical splitting does). Sub-.mmd's are concatenated in
# page order into <name>.mmd. Resumable (skips books whose .mmd exists).
set -u
V=/Users/ianzhang/UAUV/.venv-nougat/bin
REFS=/Users/ianzhang/UAUV/refs
OUT=$REFS/ocr
DASH=$OUT/dash
MODEL=0.1.0-small
WORKERS=${WORKERS:-1}      # 1 = safest for unattended overnight. 2 only if you're watching.
THREADS=${THREADS:-3}
SPLIT=${SPLIT:-15}         # pages per physical sub-PDF -> hard RAM bound (~1.5-2 GB/proc)
export PYTHONSAFEPATH=1    # + workers cd into $OUT: together they satisfy nltk's regex shim
if [ -z "${PRIO:-}" ]; then PRIO="nice -n 10"; fi   # yields to foreground, still progresses
mkdir -p "$DASH"

TODO=()
for pdf in "$REFS"/*.pdf; do b=$(basename "$pdf" .pdf); [ -f "$OUT/$b.mmd" ] || TODO+=("$pdf"); done
[ ${#TODO[@]} -eq 0 ] && { echo "nothing to do"; exit 0; }

WORKERS=$WORKERS "$V/python" - "$DASH" "$WORKERS" "$MODEL" "${TODO[@]}" <<'PY'
import sys, json, os, pypdfium2 as p
dash, W, model = sys.argv[1], int(sys.argv[2]), sys.argv[3]; files = sys.argv[4:]
items = []
for f in files:
    try: n = len(p.PdfDocument(f))
    except Exception: n = 0
    items.append((f, n))
json.dump({"files": [{"file": os.path.basename(f), "pages": n} for f, n in items],
           "total_pages": sum(n for _, n in items), "total_files": len(items),
           "workers": W, "model": model}, open(os.path.join(dash, "manifest.json"), "w"))
bins = [[] for _ in range(W)]; load = [0]*W
for f, n in sorted(items, key=lambda t: -t[1]):
    k = load.index(min(load)); bins[k].append(f); load[k] += n
for i in range(W):
    open(os.path.join(dash, "assign_w%d.txt" % (i+1)), "w").write("\n".join(bins[i]))
print("assigned %d files / %d workers; page-loads=%s (split=%s)" % (len(items), W, load, os.environ.get("SPLIT")))
PY

"$V/python" -c "from nougat.utils.checkpoint import get_checkpoint; get_checkpoint(model_tag='$MODEL')" >> "$DASH/build.log" 2>&1 || true

for w in $(seq 1 "$WORKERS"); do : > "$DASH/worker$w.log"; done
for w in $(seq 1 "$WORKERS"); do
  (
    cd "$OUT" || exit 1
    echo "worker $w started $(date)"
    while IFS= read -r book; do
      [ -z "$book" ] && continue
      b=$(basename "$book" .pdf)
      [ -f "$OUT/$b.mmd" ] && { echo "SKIP $b"; continue; }
      tmp="$OUT/.split_w$w"; rm -rf "$tmp"; mkdir -p "$tmp/src"
      "$V/python" /Users/ianzhang/UAUV/pdf_split.py "$book" "$tmp/src" "$SPLIT" || { echo "FAIL split $b"; continue; }
      nsub=$(ls "$tmp/src"/*.pdf 2>/dev/null | wc -l | tr -d ' ')
      : > "$OUT/$b.mmd.partial"; i=0
      for sub in $(ls "$tmp/src"/*.pdf 2>/dev/null | sort); do
        i=$((i+1)); odir="$tmp/out"; rm -rf "$odir"; mkdir -p "$odir"
        echo "=== WORKER$w BOOK $b SUB $i/$nsub $(date) ==="
        OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS VECLIB_MAXIMUM_THREADS=$THREADS \
          $PRIO "$V/nougat" "$sub" -o "$odir" -m "$MODEL" --batchsize 1
        mf=$(ls "$odir"/*.mmd 2>/dev/null | head -1)
        [ -n "$mf" ] && { cat "$mf" >> "$OUT/$b.mmd.partial"; printf '\n\n' >> "$OUT/$b.mmd.partial"; } || echo "WARN no output for $(basename "$sub")"
        rm -f "$sub"
      done
      mv "$OUT/$b.mmd.partial" "$OUT/$b.mmd"
      rm -rf "$tmp"
      echo "=== WORKER$w DONE $b $(date) ==="
    done < "$DASH/assign_w$w.txt"
    echo "worker $w finished $(date)"
  ) >> "$DASH/worker$w.log" 2>&1 &
done
wait
echo "rendering viewable HTML ..."
"$V/python" /Users/ianzhang/UAUV/view_ocr.py >> "$DASH/build.log" 2>&1 || true
echo "ALL OCR DONE $(date)"
