"""Clash check + service-access for the LaFengParrot standing pose.

Transforms are BAKED into the geometry with BRepBuilderAPI_Transform(...,True)
because cadquery .moved()/.located() only sets a TopLoc location that
BRepAlgoAPI_Common does not bake in.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import cadquery as cq
import registry
import poses

from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

parts = registry.all_parts()
inst = poses._INSTANCES
loc_standing = poses.standing()
row = {k: (pid, cfg, R, t) for (k, pid, cfg, R, t) in inst}


def baked(key):
    pid, cfg, R, t = row[key]
    s = parts[pid]["build"](cfg)
    tr = gp_Trsf()
    tr.SetValues(R[0][0], R[0][1], R[0][2], t[0],
                 R[1][0], R[1][1], R[1][2], t[1],
                 R[2][0], R[2][1], R[2][2], t[2])
    return BRepBuilderAPI_Transform(s.wrapped, tr, True).Shape()


def bb_of(wshape):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b = Bnd_Box()
    BRepBndLib.Add_s(wshape, b)
    return b


placed_w = {k: baked(k) for (k, *_ ) in inst}
placed_bb = {k: cq.Shape(w).BoundingBox() for k, w in placed_w.items()}


def disjoint(k1, k2):
    a, b = placed_bb[k1], placed_bb[k2]
    return not (a.xmax >= b.xmin and a.xmin <= b.xmax and
                a.ymax >= b.ymin and a.ymin <= b.ymax and
                a.zmax >= b.zmin and a.zmin <= b.zmax)


def vol_intersect(w1, w2):
    c = BRepAlgoAPI_Common(w1, w2)
    c.Build()
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(c.Shape(), g)
    return g.Mass()


# designed-intimate / excluded pair prefixes (servo-in-pocket, cable stubs)
def classify(ka, kb, v):
    # cosmetic cable/lead stubs live on servos/bec/lipo/fuse -> flag, not clash
    cable_owners = ("st3215", "sc0043", "bec", "fuse", "lipo")
    # designed matings: a servo inside its own printed pocket
    designed = [
        ("hip_mount", "st3215_hiproll"),
        ("thigh_link", "st3215_hippitch"),
        ("thigh_link", "st3215_knee"),
        ("thigh_link", "shin_link"),          # knee joint
        ("shin_link", "st3215_knee"),         # knee horn
        ("wing_arm", "sc0043_wing"),
        ("neck_linkage", "sc0043_neckyaw"),
        ("neck_linkage", "sc0043_neckpitch"),
        ("trunk_shell", "neck_linkage"),      # neck bolts to roof
        ("trunk_shell", "sc0043_neckyaw"),    # yaw servo under base plate
        ("neck_linkage", "head_shell"),       # pitch horn
        ("head_shell", "imuc"),
        ("battery_tray", "lipo"),
        ("power_mount", "xt60"),
        ("power_mount", "bec"),
        ("power_mount", "fuse"),
        ("trunk_shell", "orin_carrier"),
    ]
    for pre_a, pre_b in designed:
        if ka.startswith(pre_a) and kb.startswith(pre_b) or ka.startswith(pre_b) and kb.startswith(pre_a):
            return "CONTACT/DESIGNED"
    # cosmetic lead/cable stubs crossing (150 mm servo cables, BEC/fuse leads)
    cosmetic = {
        ("st3215_hippitch_L", "st3215_hippitch_R"),
        ("st3215_knee_L", "st3215_knee_R"),
        ("xt60_switch", "bec_5v3a"),
        ("xt60_switch", "fuse_holder"),
        ("trunk_shell", "lipo_3s_2200"),
        ("trunk_shell", "xt60_switch"),
        ("trunk_shell", "bec_5v3a"),
        ("trunk_shell", "fuse_holder"),
        ("trunk_shell", "battery_tray"),
        ("trunk_shell", "power_mount"),
    }
    if (ka, kb) in cosmetic or (kb, ka) in cosmetic:
        return "COSMETIC/LEAD"
    if v > 0.01:
        return "CLASH"
    if v > 1e-6:
        return "TOUCH"
    return "OK"


print(f"{'pair':46s} {'vol':>9s}  verdict")
nonok = []
keys = [k for (k, *_ ) in inst]
for i, ka in enumerate(keys):
    for kb in keys[i+1:]:
        if disjoint(ka, kb):
            continue
        v = vol_intersect(placed_w[ka], placed_w[kb])
        c = classify(ka, kb, v)
        if c != "OK":
            nonok.append((ka, kb, v, c))
            print(f"{(ka+' / '+kb):46s} {v:9.2f}  {c}")

print(f"\nnon-OK/designed pairs: {len(nonok)}")
# save for the report
import json
out = {"rows": [[a, b, round(v, 3), c] for (a, b, v, c) in nonok]}
pathlib.Path(HERE / "_clash_result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("saved", HERE / "_clash_result.json")
