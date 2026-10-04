"""Deterministic LaFengParrot engineering drawings (NO AI generation).

Rebuilds the standing + exploded assemblies via poses.py, tessellates the placed
solids in memory (OCP via cadquery Shape.tessellate), projects with matplotlib,
and renders:
  drawings/front.{png,svg}    orthographic  YZ  (look along +X)
  drawings/side.{png,svg}     orthographic  XZ  (look along +Y)
  drawings/exploded.{png,svg} isometric exploded (exploded() pose)
  drawings/drawings.pdf       all three pages

All dimension anchors are read from ASSEMBLY_REPORT.md / CONVENTIONS.md §6.
"""
from __future__ import annotations
import sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.backends.backend_pdf import PdfPages

import cadquery as cq

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))          # source/  (registry)
sys.path.insert(0, str(_HERE))                 # source/assembly (poses)
import registry  # noqa: E402
import poses     # noqa: E402

# Resolve from this script so generation works identically on Windows and WSL.
OUT = _HERE.parents[1] / "drawings"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Build placed instances (global-frame triangles), kept per instance.
# ---------------------------------------------------------------------------
def _local_shapes(obj):
    """Normalize a build() return to a list of cq Shape."""
    if isinstance(obj, cq.Workplane):
        return obj.vals()
    if isinstance(obj, cq.Compound):
        return list(obj.Solids()) if hasattr(obj, "Solids") else obj.solids().vals()
    if isinstance(obj, (cq.Solid, cq.Shell, cq.Face)):
        return [obj]
    return list(obj)


def build_instances(pose: str):
    """Return list of dicts: {key, pid, meta, tris:[ (3,3) global ]}."""
    locs = poses.standing() if pose == "standing" else poses.exploded()
    parts = registry.all_parts()
    out = []
    for (key, pid, cfg, R, t) in poses._INSTANCES:
        builder = parts[pid]["build"]
        solid = builder(cfg)
        placed = solid.located(locs[key])
        shapes = _local_shapes(placed)
        tris = []
        for sh in shapes:
            try:
                verts, idx = sh.tessellate(0.6)
            except Exception:
                continue
            va = np.array([[v.x, v.y, v.z] for v in verts], dtype=float)
            for tri in idx:
                pts = va[list(tri)]
                if pts.shape == (3, 3):
                    tris.append(pts)
        out.append({"key": key, "pid": pid,
                    "name": parts[pid]["meta"]["name"],
                    "tris": tris})
    return out


def collect_triangles(instances):
    """Concatenate every triangle; also return per-instance centroid."""
    alltris = []
    for inst in instances:
        alltris.extend(inst["tris"])
    return np.array(alltris, dtype=float) if alltris else np.zeros((0, 3, 3))


# ---------------------------------------------------------------------------
# 2. Projections
# ---------------------------------------------------------------------------
def project_front(P):
    """Look along +X -> horizontal = Y, vertical = Z, depth = X."""
    return P[..., 1], P[..., 2], P[..., 0]   # u=y, v=z, depth=x


def project_side(P):
    """Look along +Y -> horizontal = X, vertical = Z, depth = Y.
    Mirror X so +X (beak/front) points right (standard side view)."""
    return -P[..., 0], P[..., 2], P[..., 1]   # u=-x, v=z, depth=y


def project_iso(P):
    """Isometric-ish: yaw 45 deg about Z, pitch 30 deg about screen X."""
    a = np.radians(45.0)
    ca, sa = np.cos(a), np.sin(a)
    x1 = P[..., 0] * ca - P[..., 1] * sa
    y1 = P[..., 0] * sa + P[..., 1] * ca
    z1 = P[..., 2]
    b = np.radians(30.0)
    cb, sb = np.cos(b), np.sin(b)
    u = x1
    v = y1 * cb + z1 * sb
    depth = -y1 * sb + z1 * cb
    return u, v, depth


# ---------------------------------------------------------------------------
# 3. Draw a projected triangle cloud
# ---------------------------------------------------------------------------
def draw_mesh(ax, tris3d, proj, fc="#c3cdd6", ec="#4c5963", lw=0.25):
    u, v, d = proj(tris3d)
    # tris3d shape (N,3,3) -> u,v,d each (N,3)
    polys = np.stack([u, v], axis=-1)          # (N,3,2)
    depth = d.mean(axis=1)                      # (N,)
    order = np.argsort(depth)                   # far -> near
    pc = PolyCollection(polys[order], facecolors=fc, edgecolors=ec,
                        linewidths=lw, antialiased=True, zorder=2)
    ax.add_collection(pc)
    # bounds (tight padding so the plot fills the canvas)
    ax.set_xlim(u.min() - 12, u.max() + 12)
    ax.set_ylim(v.min() - 12, v.max() + 12)
    return u, v


def dim_h(ax, x0, x1, y, text, color="#b3202a", off=0.0, fs=9):
    """Horizontal dimension line at height y from x0..x1."""
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=1.1), zorder=5)
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom",
            fontsize=fs, color=color, zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))


def dim_v(ax, y0, y1, x, text, color="#b3202a", off=0.0, fs=9):
    """Vertical dimension line at x from y0..y1."""
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color=color, lw=1.1), zorder=5)
    ax.text(x + off, (y0 + y1) / 2, text, ha="left", va="center",
            fontsize=fs, color=color, zorder=6, rotation=90,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))


def leaders(ax, u, v, depth):
    pass


# ---------------------------------------------------------------------------
# 4. Views
# ---------------------------------------------------------------------------
def view_front(standing_tris, instances):
    fig, ax = plt.subplots(figsize=(11.5, 10.5), dpi=160)
    u, v = draw_mesh(ax, standing_tris, project_front)
    # REV-B anchors (global): hip z=0 y=+/-27; hip_pitch z=-42; knee z=-84;
    # sole floor z=-138; trunk floor 33 roof 133; neck base 133;
    # neck pitch axis z=185; crest z=256; wings y=+/-190.9.
    # --- horizontal: hip rail 54 (open gap above hip plane, below trunk floor 33)
    dim_h(ax, -27, 27, 16, "hip rail 54 mm", off=2)
    # --- horizontal: wing span (y +/-190.9), in roof->neck gap z=150
    dim_h(ax, -190.9, 190.9, 150, "wing span ~382 mm (y +/-190.9)", off=2)
    # --- vertical rails on the right (y=+72, outside trunk half-width)
    dim_v(ax, -138, 256, 72, "total height 394 mm", off=4)
    dim_v(ax, 33, 133, 60, "trunk 100 mm (33->133)", off=4)
    dim_v(ax, 133, 185, 60, "neck 52 mm (133->185)", off=4)
    dim_v(ax, 185, 256, 72, "head 71 mm (185->256)", off=4)
    # --- vertical rails on the left (y=-58, outside leg half-width)
    dim_v(ax, -42, 0, -58, "thigh 42 mm", off=-30)
    dim_v(ax, -134, -84, -58, "shin 50 mm", off=-30)
    # --- foot width 44 (one sole: L sole y[5,49]) at sole height z=-132
    dim_h(ax, 5, 49, -128, "foot 40x44 (W=44, 10 mm inner gap)", off=2)
    ax.set_title("LaFengParrot - FRONT orthographic (look along +X; Y horizontal, Z up)\n"
                 "REV-B standing zero pose, dimensions in mm. Source: ASSEMBLY_REPORT.md",
                 fontsize=11)
    ax.set_xlabel("Y (mm)  - parrot left = +Y")
    ax.set_ylabel("Z (mm)")
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3, alpha=0.4)
    fig.tight_layout()
    return fig


def view_side(standing_tris, instances):
    fig, ax = plt.subplots(figsize=(9.5, 11.5), dpi=160)
    u, v = draw_mesh(ax, standing_tris, project_side)
    # u = -x (beak +X -> screen right), v = z.
    # Vertical rails: rear (global x=-40 -> screen u=+40) and front (x=+45 -> u=-45).
    rear_u = -(-40.0)   # = 40
    front_u = -(45.0)   # = -45
    dim_v(ax, -138, 0, front_u - 10, "leg drop 138 mm", off=4)
    dim_v(ax, 33, 133, rear_u + 10, "trunk 100 mm (33->133)", off=4)
    dim_v(ax, 72, 100, front_u - 10, "carrier exhaust 28 mm (board 72->cooler 100)", off=4)
    dim_v(ax, 133, 185, rear_u + 10, "neck pitch 52 mm (133->185)", off=4)
    dim_v(ax, 185, 256, front_u - 10, "head 71 mm (185->256)", off=4)
    # foot length 40 in X (sole runs x), at sole height z=-132
    dim_h(ax, -20, 20, -128, "foot length 40 mm", off=2)
    # overall X extent (REV-B: no cosmetic 150 mm cable extremes remain)
    umin, umax = u.min(), u.max()
    dim_h(ax, umin, umax, -138 - 22,
          f"overall length ~{umax-umin:.0f} mm (x -64..+72)", off=2)
    ax.set_title("LaFengParrot - SIDE orthographic (look along +Y; -X screen-horizontal, Z up)\n"
                 "REV-B standing zero pose, beak = screen right. Dimensions in mm.", fontsize=11)
    ax.set_xlabel("screen u = -X (mm)")
    ax.set_ylabel("Z (mm)")
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3, alpha=0.4)
    fig.tight_layout()
    return fig


def view_exploded(exploded_tris, instances):
    fig, ax = plt.subplots(figsize=(14, 12), dpi=160)
    u, v = draw_mesh(ax, exploded_tris, project_iso, fc="#e3e8ec", ec="#46525c", lw=0.3)
    # Per-instance centroid callouts (part_id -> name).
    proj = project_iso
    for inst in instances:
        if not inst["tris"]:
            continue
        arr = np.array(inst["tris"])              # (N,3,3)
        cu = proj(arr)[0].mean()
        cv = proj(arr)[1].mean()
        ax.text(cu, cv, inst["pid"], fontsize=7.5, ha="center", va="center",
                color="#0b3d91", zorder=7,
                bbox=dict(boxstyle="round,pad=0.18", fc="#fff7cc", ec="#0b3d91", lw=0.6))
    ax.set_title("LaFengParrot — EXPLODED isometric (exploded() pose; parts separated >=30 mm)\n"
                 "labels = CAD part_id (see ASSEMBLY.md 1:1 BOM map). Dimensions in mm.",
                 fontsize=11)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_xlabel("isometric u")
    ax.set_ylabel("isometric v")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 5. Non-blank check
# ---------------------------------------------------------------------------
def nonblank_fraction(png_path):
    from PIL import Image
    im = np.asarray(Image.open(png_path).convert("RGB"), dtype=float)
    nonwhite = (im.sum(axis=2) < 720).mean()
    return nonwhite


# ---------------------------------------------------------------------------
def main():
    print("Building standing assembly...")
    standing = build_instances("standing")
    st = collect_triangles(standing)
    print(f"  standing: {len(standing)} instances, {len(st)} triangles, "
          f"bbox x[{st[...,0].min():.1f},{st[...,0].max():.1f}] "
          f"y[{st[...,1].min():.1f},{st[...,1].max():.1f}] "
          f"z[{st[...,2].min():.1f},{st[...,2].max():.1f}]")
    print("Building exploded assembly...")
    exploded = build_instances("exploded")
    ex = collect_triangles(exploded)
    print(f"  exploded: {len(exploded)} instances, {len(ex)} triangles")

    figs = []
    fig = view_front(st, standing);  fig.savefig(OUT/"front.png", dpi=160); fig.savefig(OUT/"front.svg"); figs.append(fig)
    fig = view_side(st, standing);   fig.savefig(OUT/"side.png", dpi=160);  fig.savefig(OUT/"side.svg");  figs.append(fig)
    fig = view_exploded(ex, exploded); fig.savefig(OUT/"exploded.png", dpi=160); fig.savefig(OUT/"exploded.svg"); figs.append(fig)

    with PdfPages(OUT/"drawings.pdf") as pdf:
        for f in figs:
            pdf.savefig(f)
    for f in figs:
        plt.close(f)

    for name in ["front.png", "side.png", "exploded.png"]:
        frac = nonblank_fraction(OUT/name)
        print(f"  {name}: non-white pixel fraction = {frac:.3f} "
              f"({'OK' if frac > 0.10 else 'TOO BLANK'})")
    print("Done ->", OUT)


if __name__ == "__main__":
    main()
