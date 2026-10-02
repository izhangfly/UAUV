# Fusion 360 script: export selected bodies to individual binary STL files.
#
# WHY THIS VERSION: Fusion's ExportManager STL exporter routes through a translation
# service that fails systemically on some setups ("RuntimeError: 2 : InternalValidationError : success").
# This script BYPASSES it: it tessellates each body LOCALLY via body.meshManager (the same
# engine that draws bodies on screen) and writes the binary STL itself. No translator, no cloud.
#
# OUTPUT: ~/UAUV/stl/<BodyName>.stl  --  binary, in METRES (already scaled; no surfaceTransformPoints needed).
#
# HOW TO RUN: Utilities -> ADD-INS -> Scripts and Add-Ins -> Scripts -> transmediumexport -> Run.

import adsk.core, adsk.fusion, traceback, os, struct

# --- EDIT THIS LIST to control what gets exported -------------------------
KEEP = [
    "NBody",                      # fuselage (with dorsal recess)
    "VFin", "HFin",               # cruciform tail fins
    "Pivot Actuator cylinder",    # structural standoff bridging wing to body -- wetted, reused every case
    "Wing0", "Wing10", "Wing20", "Wing30", "Wing40",
    "Wing50", "Wing60", "Wing70", "Wing80", "Wing90",
    # "NProp",                    # prop-OFF for the steady sweep; uncomment only for a separate propulsion study
]
OUT_DIR = os.path.expanduser("~/UAUV/stl")
CM_TO_M = 0.01                    # Fusion internal units are centimetres -> write STL in metres
# -------------------------------------------------------------------------

_TRI = struct.Struct("<12fH")     # 3 normal + 9 vertex floats + 2-byte attribute, per triangle

def _write_binary_stl(path, coords, idx):
    """coords: flat list of node xyz in cm; idx: flat list of triangle vertex indices."""
    ntri = len(idx) // 3
    buf = bytearray()
    buf += b"\0" * 80                          # 80-byte header
    buf += struct.pack("<I", ntri)             # triangle count
    s = CM_TO_M
    for t in range(ntri):
        a = 3 * idx[3 * t]; b = 3 * idx[3 * t + 1]; c = 3 * idx[3 * t + 2]
        ax, ay, az = coords[a] * s, coords[a + 1] * s, coords[a + 2] * s
        bx, by, bz = coords[b] * s, coords[b + 1] * s, coords[b + 2] * s
        cx, cy, cz = coords[c] * s, coords[c + 1] * s, coords[c + 2] * s
        # face normal via cross product
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        L = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        buf += _TRI.pack(nx / L, ny / L, nz / L, ax, ay, az, bx, by, bz, cx, cy, cz, 0)
    with open(path, "wb") as f:
        f.write(buf)
    return ntri

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("No active Fusion design.")
            return
        root = design.rootComponent

        if not os.path.exists(OUT_DIR):
            os.makedirs(OUT_DIR)

        by_name = {b.name: b for b in root.bRepBodies}   # folders are cosmetic; all root bodies here

        done, issues = [], []
        for name in KEEP:
            body = by_name.get(name)
            if body is None:
                issues.append(name + " (not found)")
                continue
            try:
                calc = body.meshManager.createMeshCalculator()
                calc.setQuality(adsk.fusion.TriangleMeshQualityOptions.HighQualityTriangleMesh)
                mesh = calc.calculate()
                safe = name.replace(" ", "_")
                path = os.path.join(OUT_DIR, safe + ".stl")
                ntri = _write_binary_stl(path, mesh.nodeCoordinatesAsDouble, mesh.nodeIndices)
                done.append("{} ({} tris)".format(safe + ".stl", ntri))
                adsk.doEvents()
            except Exception as e:
                issues.append(name + " (" + str(e) + ")")

        msg = "Exported {} STL(s) to:\n{}\n\n{}".format(len(done), OUT_DIR, "\n".join(done))
        if issues:
            msg += "\n\nISSUES:\n" + "\n".join(issues)
        ui.messageBox(msg)
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
