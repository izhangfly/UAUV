#!/usr/bin/env python3
"""Precise memory safety net for the OCR run.

The failure mode is a single nougat process ballooning (runaway token generation on a bad
page). Normal chunks sit at ~0.5-1.5 GB. So the right guard is PER-PROCESS: kill a nougat
worker only if ITS OWN resident memory exceeds a cap -- this ignores macOS parking idle apps
in swap (which is normal on a tight machine) and fires exactly on a real runaway.

A system backstop also kills all nougat if free RAM gets genuinely near-zero.
Runs detached with the main venv python (has psutil). Kills only nougat, never the launcher.
"""
import time, os, subprocess
import psutil

CAP_GB = 4.0          # kill a nougat process whose OWN RSS exceeds this (runaway; normal < 1.5)
FREE_MIN_GB = 0.6     # backstop: if free RAM drops below this, kill all nougat
LOG = os.path.expanduser("~/UAUV/refs/ocr/dash/watchdog.log")

def log(m):
    with open(LOG, "a") as f:
        f.write("%s  %s\n" % (time.strftime("%H:%M:%S"), m))

log("watchdog START (per-proc cap %.1fGB, backstop free<%.1fGB)" % (CAP_GB, FREE_MIN_GB))
while True:
    try:
        for p in psutil.process_iter(["pid", "cmdline", "memory_info"]):
            try:
                cl = " ".join(p.info.get("cmdline") or [])
                if ".venv-nougat/bin/nougat" in cl:
                    rss = p.info["memory_info"].rss / 1e9
                    if rss > CAP_GB:
                        p.kill()
                        log("!! killed runaway nougat pid %s rss=%.1fGB" % (p.pid, rss))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        vm = psutil.virtual_memory()
        if vm.available / 1e9 < FREE_MIN_GB:
            subprocess.run(["pkill", "-9", "-f", ".venv-nougat/bin/nougat"])
            log("!! BACKSTOP killed all nougat: free=%.2fGB mem=%d%%" % (vm.available / 1e9, vm.percent))
            time.sleep(6)
    except Exception as e:
        log("watchdog error: %s" % e)
    time.sleep(2)
