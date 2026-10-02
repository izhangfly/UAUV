#!/usr/bin/env python3
"""
Generate a 2-D slender-ogive nose STL for the ENTRY campaign — VERTICAL orientation.

FIXED (2026-08-03): axis is now along Z (the penetration/entry direction), not X.
  - Tip at (0, 0, 0), pointing DOWN (-Z).
  - Body extends UP (+Z): nose curve over 0..L_n, then cylindrical to L_b.
  - Radius is in X (half-width D/2).  Extruded thin in Y for the 2-D slice.

The body sits in AIR above the free surface (water at Z<0); the rising surface wets the
nose progressively.  Because the tip is a point (zero area), the t=0 impact force is ~0.

Myring nose (elliptical, n=2):  r(a) = (D/2)*sqrt(1 - ((L_n - a)/L_n)^2),  a = axial dist from tip.

Usage:  python3 create_nose_stl.py [output.stl]
"""

import sys, os, math

# --- Geometry ---
D     = 0.10    # diameter [m]  (width in X)
L_n   = 0.15    # nose length [m]
L_b   = 0.50    # modelled body length [m] (tip to tail, along +Z)
Y_w   = 0.06    # extrusion thickness in Y [m] (wider than domain Y=±0.02 so snappy cuts clean)
Z_TIP = 0.0     # Z of nose tip [m] (tip at the free surface; body in air above)
N_pts = 80      # resolution along nose curve


def myring_r(a):
    """Half-width (radius) at axial distance a from the tip (0<=a<=L_n)."""
    a = max(0.0, min(a, L_n))
    t = (L_n - a) / L_n
    return 0.5 * D * math.sqrt(1.0 - t * t)


# --- Build closed 2-D profile in the (X, Z) plane, axis along +Z ---
# Right side (X>=0), from tip upward, then across the top, down the left side.
right = []
right.append((0.0, Z_TIP))                                   # tip
for i in range(1, N_pts):
    a = L_n * i / (N_pts - 1)
    right.append((myring_r(a), Z_TIP + a))                   # nose curve
right.append((D / 2.0, Z_TIP + L_b))                         # cylindrical body side -> tail

# Left side mirrored (X -> -X), top-down, skip duplicate tail/tip endpoints
left = [(-x, z) for (x, z) in reversed(right[1:-1])]

profile = right + [(-D / 2.0, Z_TIP + L_b)] + left           # closed polygon (CCW)

# --- Extrude in Y ---
y0, y1 = -Y_w / 2.0, Y_w / 2.0
n = len(profile)
verts, faces = [], []
for (x, z) in profile:                    # front (Y=y0)
    verts.append((x, y0, z))
for (x, z) in profile:                    # back  (Y=y1)
    verts.append((x, y1, z))

for i in range(1, n - 1):                 # front cap
    faces.append((0, i, i + 1))
off = n
for i in range(1, n - 1):                 # back cap (reversed winding)
    faces.append((off, off + i + 1, off + i))
for i in range(n):                        # side walls
    j = (i + 1) % n
    faces.append((i, j, off + j))
    faces.append((i, off + j, off + i))


def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def crs(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def nrm(v):
    m = math.sqrt(sum(c*c for c in v));  return (v[0]/m, v[1]/m, v[2]/m) if m > 0 else (0, 0, 1)

output = sys.argv[1] if len(sys.argv) > 1 else "constant/triSurface/bodyNose.stl"
os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
with open(output, "w") as f:
    f.write("solid bodyNose\n")
    for t in faces:
        v0, v1, v2 = verts[t[0]], verts[t[1]], verts[t[2]]
        nx, ny, nz = nrm(crs(sub(v1, v0), sub(v2, v0)))
        f.write(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}\n    outer loop\n")
        for v in (v0, v1, v2):
            f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
        f.write("    endloop\n  endfacet\n")
    f.write("endsolid bodyNose\n")

print(f"Wrote {output}: {len(verts)} vertices, {len(faces)} triangles")
print(f"  VERTICAL ogive: D={D:.3f} m (in X), L_n={L_n:.3f} m, L_b={L_b:.3f} m (along +Z)")
print(f"  Tip at (0,0,{Z_TIP}); body extends UP to Z={Z_TIP+L_b:.3f}; enters -Z / water rises +Z")
