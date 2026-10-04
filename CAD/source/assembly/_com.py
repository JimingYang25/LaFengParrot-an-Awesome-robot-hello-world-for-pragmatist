"""REV-B CoM & statics: baked centroids, frame mass = real PETG volume x 1.27."""
import sys, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import cadquery as cq
import registry, poses
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

parts = registry.all_parts()
inst = poses._INSTANCES
row = {k: (pid, cfg, R, t) for (k, pid, cfg, R, t) in inst}
FRAME = {"battery_tray","head_shell","hip_mount","neck_linkage","power_mount",
         "shin_link","thigh_link","trunk_shell","wing_arm"}
RHO = 1.27  # g/cm3 PETG

def placed(key):
    pid, cfg, R, t = row[key]
    s = parts[pid]["build"](cfg)
    w = s.wrapped if hasattr(s, "wrapped") else s.val().wrapped
    tr = gp_Trsf()
    tr.SetValues(R[0][0], R[0][1], R[0][2], t[0],
                 R[1][0], R[1][1], R[1][2], t[1],
                 R[2][0], R[2][1], R[2][2], t[2])
    return cq.Shape(BRepBuilderAPI_Transform(w, tr, True).Shape())

mass_sum = 0.0
mom = [0.0, 0.0, 0.0]
rows = []
for (k, pid, cfg, R, t) in inst:
    sh = placed(k)
    vol_mm3 = sh.Volume()
    cm = sh.Center()
    if pid in FRAME:
        m = vol_mm3 / 1000.0 * RHO          # cm3 * g/cm3
        basis = f"vol {vol_mm3/1000:.1f}cm3 x1.27"
    else:
        m = parts[pid]["meta"]["mass_g"]
        basis = f"datasheet {m:g}g"
    mass_sum += m
    mom[0] += m * cm.x; mom[1] += m * cm.y; mom[2] += m * cm.z
    rows.append((k, pid, m, cm.x, cm.y, cm.z, basis))

# 105 g lump (fasteners/horns/bearings/wiring): convention = add at the
# running CoM so it does not bias the balance; state it.
M_LUMP = 105.0
cx, cy, cz = mom[0]/mass_sum, mom[1]/mass_sum, mom[2]/mass_sum
mass_sum += M_LUMP
# lump at CoM -> CoM unchanged

print(f"{'instance':22s} {'mass_g':>8s}  cm(x,y,z)")
for k, pid, m, x, y, z, b in rows:
    print(f"{k:22s} {m:8.1f}  ({x:7.1f},{y:7.1f},{z:7.1f})")
print(f"\nTOTAL M (without lump) = {mass_sum-M_LUMP:.1f} g")
print(f"TOTAL M (with 105g lump) = {mass_sum:.1f} g  = {mass_sum/1000:.3f} kg")
print(f"CoM global = ({cx:.1f}, {cy:.1f}, {cz:.1f})")
print(f"CoM height above floor z=-138 : {cz-(-138):.1f} mm")
print(f"CoM height above hip plane z=0: {cz:.1f} mm")

# tipping: lateral half-base 49 mm (stance outer edge), forward 20 mm
lat_half, fwd_half = 49.0, 20.0
com_floor = cz - (-138)
ang_lat = math.degrees(math.atan(lat_half / com_floor))
ang_fwd = math.degrees(math.atan(fwd_half / com_floor))
print(f"\nTipping angles (half-base / CoM_z above floor):")
print(f"  lateral  half-base {lat_half} mm -> {ang_lat:.1f} deg")
print(f"  forward  half-base {fwd_half} mm -> {ang_fwd:.1f} deg")
print(f"  binding direction: {'FORWARD (smaller angle)' if ang_fwd<ang_lat else 'LATERAL'}")

# hip_roll torque @2x safety, r=33 mm
r = 0.033  # m
req = 0.647 * (mass_sum/1000.0)   # N m @2x per task formula
stall = 2.72
print(f"\nhip_roll required @2x = 0.647 x M = {req:.3f} N m  (r=33 mm)")
print(f"C018 stall = {stall} N m -> margin {stall/req:.2f}x")
