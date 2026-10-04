"""REV-B clash check: standing + 4 dynamic poses.

Bakes transforms with BRepBuilderAPI_Transform, pairwise BRepAlgoAPI_Common with
bbox pre-filter. Classifies CLASH (>0.01 mm3) / TOUCH (>1e-6) / DESIGNED.
"""
import sys, pathlib, json, math
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import cadquery as cq
import registry, poses

from OCP.gp import gp_Trsf, gp_Ax1, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

parts = registry.all_parts()
inst = poses._INSTANCES
row = {k: (pid, cfg, R, t) for (k, pid, cfg, R, t) in inst}


def _tr(R, t):
    tr = gp_Trsf()
    tr.SetValues(R[0][0], R[0][1], R[0][2], t[0],
                 R[1][0], R[1][1], R[1][2], t[1],
                 R[2][0], R[2][1], R[2][2], t[2])
    return tr


def rot_about(px, py, pz, dx, dy, dz, deg):
    a = gp_Ax1(gp_Pnt(px, py, pz), gp_Dir(dx, dy, dz))
    tr = gp_Trsf()
    tr.SetRotation(a, math.radians(deg))
    return tr


def bake(key, base=None, post=None):
    pid, cfg, R, t = row[key]
    if base is not None:
        R, t = base
    s = parts[pid]["build"](cfg)
    w = s.wrapped if hasattr(s, "wrapped") else s.val().wrapped
    tr = _tr(R, t)
    if post is not None:
        tr = post.Multiplied(tr)   # post * tr : stand, then rotate
    return BRepBuilderAPI_Transform(w, tr, True).Shape()


def world(overrides=None, posts=None):
    """overrides: key -> (R,t) full replacement. posts: key -> gp_Trsf applied after."""
    overrides = overrides or {}
    posts = posts or {}
    out = {}
    for (k, *_ ) in inst:
        out[k] = bake(k, overrides.get(k), posts.get(k))
    return out


def bb(w):
    return cq.Shape(w).BoundingBox()


def vol_intersect(w1, w2):
    c = BRepAlgoAPI_Common(w1, w2)
    c.Build()
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(c.Shape(), g)
    return g.Mass()


DESIGNED_PAIRS = [
    ("hip_mount", "st3215_hiproll"),
    ("thigh_link", "st3215_hippitch"),
    ("thigh_link", "st3215_knee"),
    ("thigh_link", "shin_link"),
    ("shin_link", "st3215_knee"),
    ("wing_arm", "sc0043_wing"),
    ("neck_linkage", "sc0043_neckyaw"),
    ("neck_linkage", "sc0043_neckpitch"),
    ("trunk_shell", "neck_linkage"),
    ("trunk_shell", "sc0043_neckyaw"),
    ("neck_linkage", "head_shell"),
    ("neck_linkage", "imuc"),
    ("head_shell", "imuc"),
    ("head_shell", "sc0043_neckpitch"),
    ("head_shell", "sc0043_neckyaw"),
    ("battery_tray", "lipo"),
    ("power_mount", "xt60"),
    ("power_mount", "bec"),
    ("power_mount", "fuse"),
    ("trunk_shell", "orin_carrier"),
    # bolted-down bodies sitting on the trunk floor slab
    ("trunk_shell", "battery_tray"),
    ("trunk_shell", "power_mount"),
    ("trunk_shell", "lipo_3s_2200"),
    ("trunk_shell", "xt60_switch"),
    ("trunk_shell", "bec_5v3a"),
    ("trunk_shell", "fuse_holder"),
]
COSMETIC = {
    ("xt60_switch", "bec_5v3a"), ("xt60_switch", "fuse_holder"),
    # 15 mm cosmetic cable stubs crossing the sagittal plane between L/R legs
    ("st3215_hippitch_L", "st3215_hippitch_R"),
    ("st3215_knee_L", "st3215_knee_R"),
}


def classify(ka, kb, v):
    for pa, pb in DESIGNED_PAIRS:
        if (ka.startswith(pa) and kb.startswith(pb)) or (ka.startswith(pb) and kb.startswith(pa)):
            return "DESIGNED"
    if (ka, kb) in COSMETIC or (kb, ka) in COSMETIC:
        return "COSMETIC"
    if v > 0.01:
        return "CLASH"
    if v > 1e-6:
        return "TOUCH"
    return "OK"


def run_clash(name, placed):
    keys = [k for (k, *_ ) in inst]
    bbs = {k: bb(placed[k]) for k in keys}
    def disjoint(a, b):
        A, B = bbs[a], bbs[b]
        return not (A.xmax >= B.xmin and A.xmin <= B.xmax and
                    A.ymax >= B.ymin and A.ymin <= B.ymax and
                    A.zmax >= B.zmin and A.zmin <= B.zmax)
    hits = []
    for i, ka in enumerate(keys):
        for kb in keys[i+1:]:
            if disjoint(ka, kb):
                continue
            v = vol_intersect(placed[ka], placed[kb])
            c = classify(ka, kb, v)
            if c != "OK":
                hits.append((ka, kb, v, c))
    clashes = [h for h in hits if h[3] == "CLASH"]
    print(f"\n=== {name} ===  non-OK pairs={len(hits)}  CLASHes={len(clashes)}")
    for ka, kb, v, c in sorted(hits, key=lambda r: -r[2]):
        print(f"  {ka:22s} / {kb:22s}  vol={v:9.2f} mm3  {c}")
    return {"hits": [[a, b, round(v, 2), c] for a, b, v, c in hits],
            "n_clash": len(clashes)}


# ---------- build scenarios ----------
report = {}

# standing
w_stand = world()
report["standing"] = run_clash("standing", w_stand)
sbL, sbR = bb(w_stand["shin_link_L"]), bb(w_stand["shin_link_R"])
print(f"  sole L y[{sbL.ymin:.1f},{sbL.ymax:.1f}] z[{sbL.zmin:.1f}] | "
      f"sole R y[{sbR.ymin:.1f},{sbR.ymax:.1f}] | inner gap={sbL.ymin - sbR.ymax:.1f} mm")
report["standing"]["sole_inner_gap"] = round(sbL.ymin - sbR.ymax, 2)

# (b) left foot lifted 50 mm, +30 mm forward (sole at z=-88)
w_b = world(overrides={"shin_link_L": (poses.R_ID, (30.0, poses.HALF, -84.0 + 50.0))})
report["foot_lifted"] = run_clash("(b) left foot lifted 50mm + fwd 30mm", w_b)
bl = bb(w_b["shin_link_L"])
print(f"  lifted foot bbox x[{bl.xmin:.1f},{bl.xmax:.1f}] y[{bl.ymin:.1f},{bl.ymax:.1f}] z[{bl.zmin:.1f},{bl.zmax:.1f}]")
report["foot_lifted"]["lifted_sole_zmin"] = round(bl.zmin, 1)

# (c) left leg abducted: rotate thigh_L, shin_L, hippitch_L, knee_L about the
# hip_roll X axis through (0,27,0) by +20 deg.
rab = rot_about(0, poses.HALF, 0.0, 1, 0, 0, 20.0)
ab_keys = ("thigh_link_L", "shin_link_L", "st3215_hippitch_L", "st3215_knee_L")
w_c = world(posts={k: rab for k in ab_keys})
report["leg_abducted"] = run_clash("(c) left leg hip_roll +20 deg", w_c)
cl = bb(w_c["shin_link_L"])
print(f"  abducted foot bbox y[{cl.ymin:.1f},{cl.ymax:.1f}] z[{cl.zmin:.1f},{cl.zmax:.1f}] centre_y={(cl.ymin+cl.ymax)/2:.1f}")
report["leg_abducted"]["foot_centre_y"] = round((cl.ymin+cl.ymax)/2, 1)

# (d) head pitched nose-down +45 about Y through (0,0,185)
rp = rot_about(0, 0, poses.PITCH_Z, 0, 1, 0, 45.0)
w_d = world(posts={"head_shell": rp, "imuc_icm42688p": rp})
report["head_pitched"] = run_clash("(d) head pitch +45 deg nose-down", w_d)
hd = bb(w_d["head_shell"])
print(f"  head after pitch z[{hd.zmin:.1f},{hd.zmax:.1f}] x[{hd.xmin:.1f},{hd.xmax:.1f}] "
      f"roof=133 -> min clearance={hd.zmin - 133.0:.1f} mm")
report["head_pitched"]["head_zmin"] = round(hd.zmin, 1)
report["head_pitched"]["clearance_above_roof"] = round(hd.zmin - 133.0, 1)

# (e) head yawed +/-90 about Z through (0,0,185)
for deg in (90.0, -90.0):
    ry = rot_about(0, 0, poses.PITCH_Z, 0, 0, 1, deg)
    w_e = world(posts={"head_shell": ry, "imuc_icm42688p": ry})
    report[f"head_yaw_{int(deg)}"] = run_clash(f"(e) head yaw {int(deg)} deg", w_e)

pathlib.Path(HERE / "_clash_result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("\nsaved _clash_result.json")
