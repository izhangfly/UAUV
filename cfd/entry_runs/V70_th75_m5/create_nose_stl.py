#!/usr/bin/env python3
"""
Generate a 2-D Myring-nose profile STL for the ENTRY campaign.

The STL is a thin slab (extruded in Y) representing the forward half
of the UAUV body, positioned so the nose tip is at the domain centre.
snappyHexMesh cuts this from the fluid domain to create the body wall patch.

Myring nose profile (elliptical, n=2):
    r(x) = D/2 * sqrt(1 - ((L_n - x)/L_n)^2)

where x = 0 at the nose tip, x = L_n at the nose-body junction.

Pure Python — no numpy dependency.

Usage:  python3 create_nose_stl.py [output.stl]
Default: constant/triSurface/bodyNose.stl
"""

import sys, os, math

# --- Geometry parameters ---
D    = 0.10    # body diameter [m]
L_n  = 0.15    # nose length [m]
L_b  = 0.50    # total body length included [m] (half-vehicle for nose-entry)
Y_w  = 0.06    # extrusion thickness in Y [m] (slightly wider than domain Y=+-0.02)
N_pts = 80     # resolution along nose curve


def myring_r(x):
    """Radius at distance x from nose tip (0 <= x <= L_n)."""
    if x < 0:
        x = 0.0
    if x > L_n:
        x = L_n
    t = (L_n - x) / L_n
    return 0.5 * D * math.sqrt(1.0 - t * t)


def cross(a, b):
    """3-D cross product."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vec_norm(v):
    """Euclidean norm."""
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec_sub(a, b):
    """Vector subtraction."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


# --- Build profile points ---
# Nose tip at origin (0, 0, 0). Body extends in +Z (upward).
# In body-fixed entry frame, nose points toward water (-Z direction),
# so the nose is at the bottom, body extends upward.

# Half-profile vertices (right half, X >= 0), clockwise:
# nose tip -> along nose surface -> flat bottom -> right side -> top -> back to tip

half_verts_2d = []

# Nose tip
half_verts_2d.append((0.0, 0.0))

# Nose surface: z = r(x) from x=0 to x=L_n
for i in range(1, N_pts):
    x = L_n * i / (N_pts - 1)
    z = myring_r(x)
    half_verts_2d.append((x, z))

# Flat bottom: z = D/2 from x=L_n to x=L_b
half_verts_2d.append((L_b, D / 2))

# Right side upward
half_verts_2d.append((L_b, D / 2 + 0.05))

# Top cap
half_verts_2d.append((0.0, D / 2 + 0.05))

# --- Build full closed polygon (mirror left half) ---
verts_2d = []
for (x, z) in half_verts_2d:
    verts_2d.append((x, z))
# Left half in reverse (skip the duplicate nose tip)
for (x, z) in reversed(half_verts_2d[:-1]):
    verts_2d.append((-x, z))

# --- Extrude in Y to make a thin 3-D slab ---
y_min = -Y_w / 2.0
y_max = Y_w / 2.0

n_2d = len(verts_2d)
vertices = []
faces = []

# Front face (Y = y_min)
for (x, z) in verts_2d:
    vertices.append((x, y_min, z))

# Back face (Y = y_max)
for (x, z) in verts_2d:
    vertices.append((x, y_max, z))

# Triangulate front face (fan from first vertex)
for i in range(1, n_2d - 1):
    faces.append((0, i, i + 1))

# Triangulate back face (fan from first back vertex, reversed winding)
offset = n_2d
for i in range(1, n_2d - 1):
    faces.append((offset + 0, offset + i + 1, offset + i))

# Side faces (quads split into two triangles)
for i in range(n_2d):
    j = (i + 1) % n_2d
    a, b = i, j
    c, d = offset + j, offset + i
    faces.append((a, b, c))
    faces.append((a, c, d))

# --- Write STL ---
output = sys.argv[1] if len(sys.argv) > 1 else "constant/triSurface/bodyNose.stl"
os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

with open(output, "w") as f:
    f.write("solid bodyNose\n")
    for tri in faces:
        v0 = vertices[tri[0]]
        v1 = vertices[tri[1]]
        v2 = vertices[tri[2]]
        u = vec_sub(v1, v0)
        v = vec_sub(v2, v0)
        n = cross(u, v)
        norm = vec_norm(n)
        if norm > 0:
            nx, ny, nz = n[0] / norm, n[1] / norm, n[2] / norm
        else:
            nx, ny, nz = 0.0, 0.0, 1.0
        f.write(f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}\n")
        f.write("    outer loop\n")
        f.write(f"      vertex {v0[0]:.6e} {v0[1]:.6e} {v0[2]:.6e}\n")
        f.write(f"      vertex {v1[0]:.6e} {v1[1]:.6e} {v1[2]:.6e}\n")
        f.write(f"      vertex {v2[0]:.6e} {v2[1]:.6e} {v2[2]:.6e}\n")
        f.write("    endloop\n")
        f.write("  endfacet\n")
    f.write("endsolid bodyNose\n")

print(f"Wrote {output}: {len(vertices)} vertices, {len(faces)} triangles")
print(f"  Body: D={D:.3f}m, L_n={L_n:.3f}m, L_body={L_b:.3f}m")
print(f"  Nose tip at (0, 0, 0), body extends in +Z")
