#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_meshes.py — LaFengParrot REV-B per-link mesh + inertial export.

Bakes the REAL CadQuery solids from CAD/source, groups them by link per
robot_description/kinematics.json, exports:
  meshes/visual/<link>.stl        visual mesh (cq.exporters.export STL)
  meshes/collision/<link>_col.stl convex hull of the merged link mesh
  inertials.json                  per-link mass / CoM / inertia (kg*m^2)

Convention: each instance solid is built in its own part-local frame, then the
assembly pose (R, t_global) from CAD/source/assembly/poses.py is BAKED into the
geometry via BRepBuilderAPI_Transform (Shape.located/.moved do NOT bake), and the
link frame_origin is subtracted so the result sits in the link's own frame with
identity rotation at the zero pose:  v_link = R @ v_local + t_global - frame_origin.

Mass:
  * printed PETG frame parts  : real volume (cm^3) * 1.27 g/cm^3
  * purchased hardware        : fixed datasheet/META mass (HW_MASS below)
Inertia: per-instance trimesh.moment_inertia (uniform density over the real
solid) scaled by actual mass/volume, then parallel-axis summed about the link
origin, then shifted to the link CoM. The 105 g build lump is distributed by
link mass fraction [EST] and placed at each link CoM (so it rescales mass and
leaves CoM/inertia about CoM unchanged).
"""
from __future__ import annotations

import importlib.util  # noqa: F401  (py3.14 explicit, as required)
import json
import math
import pathlib
import sys
import time

import numpy as np
import cadquery as cq
import trimesh
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

# ---------------------------------------------------------------- paths
HERE = pathlib.Path(__file__).resolve().parent            # robot_description
ROOT = HERE.parent                                       # LaFengParrot
CAD = ROOT / "CAD"
SRC = CAD / "source"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SRC / "lib"))
sys.path.insert(0, str(SRC / "assembly"))

import registry  # noqa: E402
import poses  # noqa: E402

KIN_PATH = HERE / "kinematics.json"
DIM_PATH = CAD / "dims" / "dimensions.json"
VIS_DIR = HERE / "meshes" / "visual"
COL_DIR = HERE / "meshes" / "collision"
INERT_PATH = HERE / "inertials.json"
VIS_DIR.mkdir(parents=True, exist_ok=True)
COL_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- knobs
LINEAR_DEFLECTION = 0.4     # mm tessellation chord tolerance
ANGULAR_DEFLECTION = 0.2    # rad
PETG_RHO = 1.27             # g/cm^3
LUMP_G = 105.0
FLOOR_Z_MM = -138.0         # sole underside in global frame (zero pose)

# purchased-hardware fixed masses (g) [dimensions.json / task brief]
HW_MASS = {
    "st3215_c018": 55.0,
    "sc0043_c001": 6.6,
    "orin_carrier": 175.0,
    "lipo_3s_2200": 185.0,
    "bec_5v3a": 15.0,
    "xt60_switch": 30.0,
    "fuse_holder": 10.0,
    "imuc_icm42688p": 4.0,
}

# ---------------------------------------------------------------- load
kin = json.loads(KIN_PATH.read_text(encoding="utf-8"))
dim = json.loads(DIM_PATH.read_text(encoding="utf-8"))
parts = registry.all_parts()

# key -> (part_id, cfg, R, t)
INST = {k: (pid, cfg, R, t) for (k, pid, cfg, R, t) in poses._INSTANCES}


def bake(shape: cq.Shape, R, t_link) -> cq.Shape:
    """Bake pose (R, translation in link frame) into the geometry."""
    tr = gp_Trsf()
    tr.SetValues(
        R[0][0], R[0][1], R[0][2], t_link[0],
        R[1][0], R[1][1], R[1][2], t_link[1],
        R[2][0], R[2][1], R[2][2], t_link[2],
    )
    out = BRepBuilderAPI_Transform(shape.wrapped, tr, True).Shape()
    return cq.Shape(out)


def as_shape(s) -> cq.Shape:
    if isinstance(s, cq.Workplane):
        s = s.val()
    return s


def mass_for(part_id: str, vol_mm3: float) -> tuple[float, str]:
    """returns (mass_g, source_tag)"""
    if part_id in HW_MASS:
        return HW_MASS[part_id], "hardware"
    return vol_mm3 / 1000.0 * PETG_RHO, f"PETG {PETG_RHO}"


def par_axis(I: np.ndarray, m: float, r: np.ndarray) -> np.ndarray:
    """parallel-axis: inertia about point O given inertia about com (I) and r=com-O."""
    return I + m * (np.dot(r, r) * np.eye(3) - np.outer(r, r))


# ---------------------------------------------------------------- build
report = {"instances_missing": [], "instances_failed": [], "links": {}}
link_results = {}   # name -> dict

for link in kin["links"]:
    lname = link["name"]
    o = np.array(link["frame_origin"], dtype=float)
    baked_shapes = []          # cq.Shape (link frame)
    trimeshes = []             # per-instance trimesh (link frame)
    breakdown = {}             # instance -> mass_g

    M = 0.0
    Cnum = np.zeros(3)
    I_O = np.zeros((3, 3))

    for key in link["instances"]:
        if key not in INST:
            report["instances_missing"].append(f"{lname}:{key}")
            continue
        part_id, cfg, R, t = INST[key]
        if part_id not in parts:
            report["instances_missing"].append(f"{lname}:{key}->{part_id}")
            continue
        try:
            solid = as_shape(parts[part_id]["build"](cfg))
            t_link = (t[0] - o[0], t[1] - o[1], t[2] - o[2])
            baked = bake(solid, R, t_link)
        except Exception as exc:  # noqa: BLE001
            report["instances_failed"].append(f"{lname}:{key} ({part_id}): {exc}")
            continue

        baked_shapes.append(baked)

        # ---- tessellate for inertial + collision
        try:
            V, F = baked.tessellate(LINEAR_DEFLECTION, ANGULAR_DEFLECTION)
            V = np.array([[float(v.x), float(v.y), float(v.z)] for v in V], dtype=float)
            F = np.asarray(F, dtype=int).reshape(-1, 3)
            tm = trimesh.Trimesh(vertices=V, faces=F, process=False)
            trimeshes.append(tm)
        except Exception as exc:  # noqa: BLE001
            report["instances_failed"].append(f"{lname}:{key} tessellate: {exc}")
            continue

        vol = abs(float(tm.volume))
        mass, mtag = mass_for(part_id, vol)
        breakdown[key] = round(mass, 3)

        com = np.asarray(tm.center_mass, dtype=float)      # mm, link frame
        I_unit = np.asarray(tm.moment_inertia, dtype=float)  # mm^5 about com, rho=1
        I_com = I_unit * (mass / vol)                        # g*mm^2
        I_O += par_axis(I_com, mass, com)
        M += mass
        Cnum += mass * com

    # ---- link CoM + inertia about CoM (mm / g*mm^2)
    C = Cnum / M
    I_C = I_O - par_axis(np.zeros((3, 3)), M, C)  # = I_O - M*(|C|^2 E - C C^T)
    I_C_kgm2 = I_C * 1e-9                          # g*mm^2 -> kg*m^2

    # ---- combined bbox (link frame)
    xs, ys, zs = [], [], []
    for b in baked_shapes:
        bb = b.BoundingBox()
        xs += [bb.xmin, bb.xmax]
        ys += [bb.ymin, bb.ymax]
        zs += [bb.zmin, bb.zmax]
    bbox = {
        "xmin": round(min(xs), 2), "xmax": round(max(xs), 2),
        "ymin": round(min(ys), 2), "ymax": round(max(ys), 2),
        "zmin": round(min(zs), 2), "zmax": round(max(zs), 2),
    }

    link_results[lname] = {
        "mass_cad_g": M, "com_mm": C, "I_C_gmm2": I_C,
        "baked": baked_shapes, "trimeshes": trimeshes,
        "breakdown": breakdown, "bbox": bbox, "frame_origin": o,
    }

# ---------------------------------------------------------------- lump distribution
M_cad_total = sum(r["mass_cad_g"] for r in link_results.values())
for lname, r in link_results.items():
    frac = r["mass_cad_g"] / M_cad_total
    r["lump_g"] = LUMP_G * frac
    r["mass_g"] = r["mass_cad_g"] + r["lump_g"]   # lump at link CoM: C/I unchanged

# ---------------------------------------------------------------- visual + collision export
mesh_files = []
for lname, r in link_results.items():
    vpath = VIS_DIR / f"{lname}.stl"
    cq.exporters.export(
        [b for b in r["baked"]], str(vpath), exportType="STL",
        tolerance=LINEAR_DEFLECTION, angularTolerance=ANGULAR_DEFLECTION, unit="MM",
    )
    # merged visual trimesh -> convex hull collision
    merged = trimesh.util.concatenate(r["trimeshes"]) if r["trimeshes"] else None
    r["n_faces"] = int(len(merged.faces)) if merged else 0
    r["vis_bytes"] = vpath.stat().st_size
    cpath = COL_DIR / f"{lname}_col.stl"
    if merged is not None:
        hull = merged.convex_hull
        hull.export(str(cpath))
        r["n_hull_faces"] = int(len(hull.faces))
        r["col_bytes"] = cpath.stat().st_size
    else:
        r["n_hull_faces"] = 0
        r["col_bytes"] = 0
    mesh_files.append((vpath, cpath))

# ---------------------------------------------------------------- reconciliation
M_final_total = sum(r["mass_g"] for r in link_results.values())
Cg_num = np.zeros(3)
for lname, r in link_results.items():
    C_global = r["com_mm"] + r["frame_origin"]     # mm, global frame
    Cg_num += r["mass_g"] * C_global
C_global = Cg_num / M_final_total
com_height_mm = C_global[2] - FLOOR_Z_MM

# ---------------------------------------------------------------- write inertials.json
out = {
    "name": "lafengparrot_inertials",
    "version": "REV-B 2026-09-27",
    "units": {"mass": "g", "length": "mm", "length_m": "m", "inertia": "kg*m^2"},
    "petg_density_g_cm3": PETG_RHO,
    "tessellation": {"linear_deflection_mm": LINEAR_DEFLECTION,
                     "angular_deflection_rad": ANGULAR_DEFLECTION},
    "lump_g": LUMP_G,
    "lump_note": ("105 g build lump [EST] distributed by link mass fraction, placed at "
                  "each link CoM: rescales mass only; link CoM and inertia-about-CoM unchanged."),
    "hardware_mass_source": HW_MASS,
    "links": {},
    "reconciliation": {
        "total_mass_g": round(M_final_total, 2),
        "total_mass_kg": round(M_final_total / 1000.0, 4),
        "target_mass_kg": 1.485,
        "cad_mass_g": round(M_cad_total, 2),
        "lump_total_g": round(sum(r["lump_g"] for r in link_results.values()), 2),
        "global_com_mm": [round(float(x), 2) for x in C_global],
        "com_height_above_floor_mm": round(float(com_height_mm), 2),
        "target_com_height_mm": 162.5,
        "floor_z_mm": FLOOR_Z_MM,
        "convention": "global CoM = sum(m_i*(com_link_i+frame_origin_i))/sum(m_i); "
                      "height = global z - floor_z(-138 mm).",
    },
}
for lname, r in link_results.items():
    out["links"][lname] = {
        "mass_g": round(r["mass_g"], 3),
        "mass_cad_g": round(r["mass_cad_g"], 3),
        "lump_g": round(r["lump_g"], 3),
        "com_mm": [round(float(x), 3) for x in r["com_mm"]],
        "com_m": [round(float(x) / 1000.0, 6) for x in r["com_mm"]],
        "inertia_kgm2": [[round(float(x), 9) for x in row] for row in r["I_C_gmm2"] * 1e-9],
        "bbox_mm": r["bbox"],
        "bbox_m": {k: round(v / 1000.0, 6) for k, v in r["bbox"].items()},
        "frame_origin_mm": [float(x) for x in r["frame_origin"]],
        "mass_breakdown_g": r["breakdown"],
        "visual_faces": r["n_faces"],
        "collision_hull_faces": r["n_hull_faces"],
    }

INERT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------------------------------------------------------- console report
print("=" * 78)
print(f"{'link':<10}{'mass_g':>9}{'lump':>7}{'comZ_mm':>10}{'zmin':>8}{'zmax':>8}"
      f"{'faces':>8}{'KB':>8}")
for lname, r in link_results.items():
    print(f"{lname:<10}{r['mass_g']:>9.1f}{r['lump_g']:>7.1f}"
          f"{r['com_mm'][2]:>10.1f}{r['bbox']['zmin']:>8.1f}{r['bbox']['zmax']:>8.1f}"
          f"{r['n_faces']:>8}{r['vis_bytes']/1024:>8.0f}")
print("-" * 78)
print(f"CAD mass        : {M_cad_total:.1f} g")
print(f"Total (incl lump): {M_final_total:.1f} g  (target 1485 g)")
print(f"Global CoM (mm) : {C_global[0]:.2f}, {C_global[1]:.2f}, {C_global[2]:.2f}")
print(f"CoM height above floor: {com_height_mm:.2f} mm  (target 162.5 mm)")
print("missing :", report["instances_missing"] or "none")
print("failed  :", report["instances_failed"] or "none")
print(f"wrote {INERT_PATH}")
for vp, cp in mesh_files:
    print(f"  {time.strftime('%H:%M:%S')}  {vp.stat().st_size/1024:8.0f} KB  {vp.name}")
    print(f"  {time.strftime('%H:%M:%S')}  {cp.stat().st_size/1024:8.0f} KB  {cp.name}")
