"""Probe: build every registry part and print measured bbox / type / volume.
Verifies the part agents' claimed local frames before placing anything."""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # so `import registry` works
import cadquery as cq
import registry

parts = registry.all_parts(refresh=True)

# extra cfgs we want to inspect
EXTRA = {
    "wing_arm": [{"side": "L"}, {"side": "R"}],
    "hip_mount": [{"side": "L"}],
    "thigh_link": [{"side": "L"}],
    "shin_link": [{"side": "L"}],
}

def show(pid, cfg, shape):
    bb = shape.BoundingBox()
    vol = shape.Volume()
    print(f"--- {pid}  cfg={cfg}  type={type(shape).__name__}  valid={shape.isValid()}")
    print(f"    bbox x[{bb.xmin:8.3f},{bb.xmax:8.3f}]  y[{bb.ymin:8.3f},{bb.ymax:8.3f}]  z[{bb.zmin:8.3f},{bb.zmax:8.3f}]")
    print(f"    size dx={bb.xmax-bb.xmin:8.3f} dy={bb.ymax-bb.ymin:8.3f} dz={bb.zmax-bb.zmin:8.3f}  vol={vol:10.2f} mm3")

for pid, info in sorted(parts.items()):
    cfgs = EXTRA.get(pid, [None])
    for cfg in cfgs:
        try:
            shape = info["build"](cfg)
            show(pid, cfg, shape)
        except Exception as e:
            print(f"!!! {pid} cfg={cfg} BUILD FAILED: {type(e).__name__}: {e}")
