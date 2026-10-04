#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_urdf.py: strict XML + urdfpy consistency check against the frozen source."""
import os, json, math, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
URDF_PATH = os.path.join(HERE, "urdf", "lafengparrot.urdf")
KIN = os.path.join(HERE, "kinematics.json")

import xml.etree.ElementTree as ET

# 1) strict XML well-formedness + raw count
tree = ET.parse(URDF_PATH)
root = tree.getroot()
assert root.tag == "robot" and root.attrib["name"] == "lafengparrot"
xml_links = root.findall("link")
xml_joints = root.findall("joint")
print(f"[xml.etree] well-formed OK; links={len(xml_links)} joints={len(xml_joints)}")

with open(KIN, encoding="utf-8") as f:
    kin = json.load(f)

# 2) urdfpy
spec = importlib.util.find_spec("urdfpy")
assert spec is not None, "urdfpy not importable"
from urdfpy import URDF
r = URDF.load(URDF_PATH)
print(f"[urdfpy] links={len(r.links)} joints={len(r.joints)}")
assert len(r.links) == 11, f"expected 11 links, got {len(r.links)}"
assert len(r.joints) == 10, f"expected 10 joints, got {len(r.joints)}"

# root has no parent joint
jmap = {j.name: j for j in r.joints}
child_links = {j.child for j in r.joints}
roots = [lk.name for lk in r.links if lk.name not in child_links]
print("[urdfpy] root link(s):", roots)
assert len(roots) == 1 and roots[0] == "base_link"

# 3) assert 10/10 joints: axis / parent-relative origin / limits vs kinematics.json
def close(a, b, tol=1e-6):
    return all(abs(float(x) - float(y)) < tol for x, y in zip(a, b))

frame_origin_mm = {lk["name"]: lk["frame_origin"] for lk in kin["links"]}
checked = 0
for kj in kin["joints"]:
    name = kj["name"]
    assert name in jmap, f"missing joint {name}"
    j = jmap[name]
    # axis
    assert close(j.axis, kj["axis"], 1e-6), f"{name} axis mismatch {j.axis} vs {kj['axis']}"
    # origin: URDF parent-relative == child frame global - parent frame global (mm->m)
    exp_rel_m = [(frame_origin_mm[kj["child"]][i] - frame_origin_mm[kj["parent"]][i]) / 1000.0
                 for i in range(3)]
    o = j.origin[:3, 3]
    assert close(o, exp_rel_m, 1e-9), f"{name} origin {o} vs parent-rel {exp_rel_m}"
    # limits
    assert abs(j.limit.lower - math.radians(kj["limit_deg"][0])) < 1e-6, f"{name} lower"
    assert abs(j.limit.upper - math.radians(kj["limit_deg"][1])) < 1e-6, f"{name} upper"
    assert abs(j.limit.effort - kj["effort_nm"]) < 1e-9, f"{name} effort"
    assert abs(j.limit.velocity - math.radians(kj["velocity_deg_s"])) < 1e-6, f"{name} velocity"
    checked += 1
print(f"[urdfpy] joint axis/origin(parent-rel)/limit match: {checked}/10")
assert checked == 10

# 4) zero-pose forward kinematics via urdfpy: every link's world origin must
#    equal the source global frame_origin (proves parent-relative origins are correct)
fk = r.link_fk()  # {Link: 4x4} at all-zero config
fk_pos = {lk.name: M[:3, 3] for lk, M in fk.items()}
print("[zero-pose FK] link world origin (m) vs source frame_origin (m):")
worst = 0.0
for lk in kin["links"]:
    nm = lk["name"]
    uname = "base_link" if nm == "trunk" else nm
    got = fk_pos[uname]
    exp = [v / 1000.0 for v in lk["frame_origin"]]
    err = max(abs(got[i] - exp[i]) for i in range(3))
    worst = max(worst, err)
    print(f"   {uname:10s} got=({got[0]:+.4f},{got[1]:+.4f},{got[2]:+.4f}) "
          f"exp=({exp[0]:+.4f},{exp[1]:+.4f},{exp[2]:+.4f}) err={err:.2e}")
assert worst < 1e-9, f"FK mismatch, worst err={worst}"
print(f"[zero-pose FK] max deviation from source frame_origin = {worst:.2e} m  OK")

print("ALL URDF CHECKS PASSED")
