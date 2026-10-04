"""REV-B export: full standing/exploded STEP + per-part local STEP/STL."""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import cadquery as cq
import registry, poses

ROOT = HERE.parent.parent
STEP_DIR = ROOT / "exports" / "step"
STL_DIR = ROOT / "exports" / "stl"
STEP_DIR.mkdir(parents=True, exist_ok=True)
STL_DIR.mkdir(parents=True, exist_ok=True)

parts = registry.all_parts()

# --- full assemblies ---
for pose, name in (("standing", "LaFengParrot_Standing"),
                   ("exploded", "LaFengParrot_Exploded")):
    asm = poses.build_assembly(pose)
    cq.exporters.export(asm, str(STEP_DIR / f"{name}.STEP"))
    bb = asm.BoundingBox()
    print(f"{name}.STEP  bbox x[{bb.xmin:.1f},{bb.xmax:.1f}] y[{bb.ymin:.1f},{bb.ymax:.1f}] z[{bb.zmin:.1f},{bb.zmax:.1f}]")

# --- per-part local frame (skip the fastener catalog) ---
SKIP = {"fastener_m2"}
EXPORT_CFG = {"wing_arm": [{"side": "L"}, {"side": "R"}]}
for pid, info in sorted(parts.items()):
    if pid in SKIP:
        continue
    cfgs = EXPORT_CFG.get(pid, [None])
    for cfg in cfgs:
        solid = info["build"](cfg)
        out_id = f"{pid}_{cfg['side']}" if cfg else pid
        cq.exporters.export(solid, str(STEP_DIR / f"{out_id}.STEP"))
        cq.exporters.export(solid, str(STL_DIR / f"{out_id}.stl"))
        print(f"  {out_id}.STEP/.stl")

print("done")
