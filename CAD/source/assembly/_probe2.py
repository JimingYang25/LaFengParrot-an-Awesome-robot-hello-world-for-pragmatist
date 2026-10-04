"""Probe: build every registry part, print bbox + volume + centroid (local frame)."""
import sys, pathlib
_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import cadquery as cq
import registry

parts = registry.all_parts(refresh=True)
print("=== REGISTRY PART IDS (%d) ===" % len(parts))
for pid, info in sorted(parts.items()):
    print(" -", pid, "| qty", info["meta"].get("qty"), "| mass", info["meta"].get("mass_g"))

CFGS = {
    "hip_mount": {"side": "L"},
    "thigh_link": {"side": "L"},
    "shin_link": {"side": "L"},
    "wing_arm": {"side": "L"},
}
print("\n=== LOCAL BBOXES / VOLUMES ===")
for pid, info in sorted(parts.items()):
    cfg = CFGS.get(pid)
    try:
        s = info["build"](cfg)
        if isinstance(s, cq.Workplane):
            s = s.val()
        bb = s.BoundingBox()
        # volume + centroid via GProp
        vol = s.Volume()
        cm = s.Center()
        print(f"{pid:20s} x[{bb.xmin:8.2f},{bb.xmax:8.2f}] y[{bb.ymin:8.2f},{bb.ymax:8.2f}] "
              f"z[{bb.zmin:8.2f},{bb.zmax:8.2f}] vol={vol:12.1f} mm3 cm=({cm.x:.2f},{cm.y:.2f},{cm.z:.2f})")
    except Exception as e:
        print(f"{pid:20s} ERROR {e}")
