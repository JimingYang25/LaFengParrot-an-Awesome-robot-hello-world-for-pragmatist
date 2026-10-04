"""Cross-format consistency check: MJCF / URDF / USD vs kinematics.json (canonical order).
Units: MJCF XML uses DEGREES for joint range (compiler angle=degree); URDF/USD use RADIANS.
USD (binary crate) is read via the pxr API.
Run:  python robot_description/verify_cross.py
"""
import json, re, pathlib, math, xml.etree.ElementTree as ET

RD = pathlib.Path(__file__).resolve().parent
K = json.loads((RD / "kinematics.json").read_text(encoding="utf-8"))
CANON = [(j["name"], tuple(j["axis"]), j["limit_deg"][0], j["limit_deg"][1]) for j in K["joints"]]
D2R = math.pi / 180.0

# ---------------- MJCF (range in DEGREES; joints in XML tree order) ----------------
mj = ET.parse(RD / "mjcf" / "lafengparrot.xml").getroot()
mj_joints = []
for j in mj.iter("joint"):
    name = j.get("name")
    if name and not name.startswith("free"):
        lo, hi = (float(x) for x in j.get("range", "0 0").split())
        ax = tuple(float(x) for x in j.get("axis", "1 0 0").split())
        mj_joints.append((name, ax, lo, hi))

# ---------------- URDF (radians) ----------------
ur = ET.parse(RD / "urdf" / "lafengparrot.urdf").getroot()
ur_joints = []
for j in ur.iter("joint"):
    if j.get("type") != "revolute":
        continue
    ax = tuple(float(x) for x in j.find("axis").get("xyz").split())
    lim = j.find("limit")
    ur_joints.append((j.get("name"), ax, float(lim.get("lower")), float(lim.get("upper"))))

# ---------------- USD (radians; binary crate — read via pxr API) ----------------
from pxr import Usd
stage = Usd.Stage.Open(str(RD / "usd" / "lafengparrot.usd"))
AXIS_TOK = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}
usd_joints = []
for prim in stage.Traverse():
    if prim.GetTypeName() != "PhysicsRevoluteJoint":
        continue
    name = prim.GetName()
    ax = prim.GetAttribute("physics:axis").Get()
    lo = prim.GetAttribute("physics:lowerLimit").Get()
    hi = prim.GetAttribute("physics:upperLimit").Get()
    if isinstance(ax, str) and ax in AXIS_TOK:
        axv = AXIS_TOK[ax]
    elif ax is not None:
        axv = tuple(float(x) for x in ax)
    else:
        axv = None
    usd_joints.append((name, axv,
                       float(lo) if lo is not None else None,
                       float(hi) if hi is not None else None))

# ---------------- compare (per-name, order-independent; then order) ----------------
def check(fmt, got, unit_deg):
    issues = []
    by_name = {}
    for (n, a, lo, hi) in got:
        by_name[n] = (a, lo, hi)
    gnames = [n for (n, *_ ) in got]
    missing = [n for (n, *_ ) in CANON if n not in by_name]
    extra = [n for n in by_name if n not in dict((n, 1) for (n, *_ ) in CANON)]
    if missing: issues.append("missing joints: %s" % missing)
    if extra: issues.append("extra joints: %s" % extra)
    for (en, ea, elo, ehi) in CANON:
        if en not in by_name: continue
        a, lo, hi = by_name[en]
        # MJCF XML joint range is authored in DEGREES (compiler angle=degree);
        # URDF/USD ranges are in RADIANS. Expected values converted accordingly.
        scale = 1.0 if unit_deg else D2R
        elo_r, ehi_r = elo * scale, ehi * scale
        if a is None:
            issues.append("%s: axis/limits not found in file" % en); continue
        if any(abs(x - y) > 1e-6 for x, y in zip(a, ea)):
            issues.append("%s axis %s != %s" % (en, a, ea))
        if abs(lo - elo_r) > 1e-6 or abs(hi - ehi_r) > 1e-6:
            issues.append("%s range [%.4f,%.4f] != expected [%.4f,%.4f]" % (en, lo, hi, elo_r, ehi_r))
    order_ok = gnames == [n for (n, *_ ) in CANON]
    return issues, order_ok, gnames

summary = {}
for fmt, got, deg in (("MJCF", mj_joints, True), ("URDF", ur_joints, False), ("USD", usd_joints, False)):
    issues, order_ok, gnames = check(fmt, got, deg)
    verdict = "PASS" if not issues else "FAIL: " + "; ".join(issues[:4]) + (" (+%d more)" % max(0, len(issues)-4) if len(issues) > 4 else "")
    print("%-5s content -> %s" % (fmt, verdict))
    if fmt == "MJCF":
        # MuJoCo assigns qpos order by tree DFS = leg-major; actuator order is canonical.
        # Verify: (a) same 10 names, (b) actuator list order canonical (checked by reading <actuator> elements).
        act = [a.get("joint") for a in mj.iter("position")]
        act_ok = act == [n for (n, *_ ) in CANON]
        print("%-5s order  -> qpos=DFS leg-major: %s (documented); actuator order canonical: %s" % (fmt, str(gnames), "PASS" if act_ok else "FAIL " + str(act)))
        summary[fmt] = (not issues) and act_ok
    elif fmt == "USD":
        # USD joints live at their attachment scopes (hierarchy-embedded DFS order);
        # content equality (names/axes/limits) is the contract; order is resolved by name in Isaac.
        nameset_ok = sorted(gnames) == sorted(n for (n, *_ ) in CANON)
        print("%-5s order  -> hierarchy-embedded: %s (10 names present: %s)" % (fmt, "PASS" if nameset_ok else "FAIL", str(gnames)))
        summary[fmt] = (not issues) and nameset_ok
    else:
        print("%-5s order  -> %s" % (fmt, "PASS (canonical)" if order_ok else "DIFFERS: " + str(gnames)))
        summary[fmt] = (not issues) and order_ok

print("---")
print("ALL THREE FORMATS CONSISTENT with kinematics.json" if all(summary.values())
      else "MISMATCH — see above")
