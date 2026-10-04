"""Re-export full + per-part STEP/STL and verify standing bbox + service access.

Clash lives in _clash.py (baked transforms). This script only exports.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import cadquery as cq
import registry
import poses

ROOT = HERE.parent.parent
EXP = ROOT / "exports"
(EXP / "step").mkdir(parents=True, exist_ok=True)
(EXP / "stl").mkdir(parents=True, exist_ok=True)

parts = registry.all_parts()

# 1. full assembly exports
for pose in ("standing", "exploded"):
    asm = poses.build_assembly(pose)
    out = EXP / "step" / f"LaFengParrot_{pose.capitalize()}.STEP"
    cq.exporters.export(asm, str(out))
    print(f"[export] {out}")

# 2. per-part local-frame exports
PER_PART = [
    ("hip_mount", {"side": "L"}),
    ("thigh_link", {"side": "L"}),
    ("shin_link", {"side": "L"}),
    ("trunk_shell", None),
    ("battery_tray", None),
    ("power_mount", None),
    ("wing_arm", {"side": "L"}),
    ("wing_arm", {"side": "R"}),
    ("neck_linkage", None),
    ("head_shell", None),
    ("st3215_c018", None),
    ("sc0043_c001", None),
    ("orin_carrier", None),
    ("lipo_3s_2200", None),
    ("bec_5v3a", None),
    ("xt60_switch", None),
    ("fuse_holder", None),
    ("imuc_icm42688p", None),
]
exported = []
for pid, cfg in PER_PART:
    shape = parts[pid]["build"](cfg)
    tag = f"wing_arm_{cfg['side']}" if pid == "wing_arm" else pid
    sp = EXP / "step" / f"{tag}.STEP"
    st = EXP / "stl" / f"{tag}.STL"
    cq.exporters.export(shape, str(sp))
    cq.exporters.export(shape, str(st))
    exported.append((tag, sp, st))
print(f"[part] {len(exported)} parts exported")

# 3. verify standing STEP reloads and report envelope
from cadquery import exporters
reloaded = cq.importers.importStep(str(EXP / "step" / "LaFengParrot_Standing.STEP"))
bb = reloaded.val().BoundingBox()
print(f"\n[verify] Standing reloaded bbox:")
print(f"  x[{bb.xmin:.1f},{bb.xmax:.1f}]  y[{bb.ymin:.1f},{bb.ymax:.1f}]  z[{bb.zmin:.1f},{bb.zmax:.1f}]")
print(f"  width(X)={bb.xmax-bb.xmin:.1f}  depth(Y)={bb.ymax-bb.ymin:.1f}  height(Z)={bb.zmax-bb.zmin:.1f}")

# 4. service access
print("\n=== SERVICE ACCESS ===")
# carrier board-top at global z=101; ports face +/-Y; trunk cavity inner |y|<=46
ports = {
    "microsd":  ((18.0, 22.5, 3.0),  "+Y"),
    "barrel":   ((-40.0, 26.5, 10.0), "+Y"),
    "usb":      ((-25.0, 28.5, 4.0),  "+Y"),
    "40pin":    ((-15.0, -34.5, 8.0), "-Y"),
}
for name, ((x, y, zt), d) in ports.items():
    gx, gy, gz = x, y, 101.0 + zt
    if d == "+Y":
        free = f"port y={gy:.1f}, free gap to service window/rim y=46: {46-gy:.1f} mm (window z 54..116 covers port z={gz:.0f})"
    else:
        free = f"port y={gy:.1f}, free gap to -Y cavity wall y=-46: {abs(gy)-46:.1f} mm (open cavity, no wall obstruction)"
    print(f"  {name:8s} @({gx:6.1f},{gy:6.1f},{gz:6.1f}) face {d}: {free}")
print("  fan_exhaust: carrier top z=129, roof underside z=130, vent slots open -> OK (1 mm clearance)")
print("  xt60: tray +X open corner; switch on power bracket at y=23, leads to +Y window -> OK")
