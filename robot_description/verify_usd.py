#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify the generated lafengparrot.usd against kinematics.json."""
import json, math, os
from pxr import Usd, UsdGeom, UsdPhysics, Sdf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "usd", "lafengparrot.usd")
kin  = json.load(open(os.path.join(HERE, "kinematics.json"), encoding="utf-8"))

stage = Usd.Stage.Open(OUT)
assert stage, "could not open"
root = stage.GetDefaultPrim()
print("root:", root.GetPath(), root.GetTypeName())

# 1) articulation root API
has_art = root.HasAPI(UsdPhysics.ArticulationRootAPI)
print("ArticulationRootAPI on root:", has_art)

# 2) link rigid bodies
link_names = [l["name"] for l in kin["links"]]
rb_count = 0
for name in link_names:
    # find prim by name anywhere
    found = None
    for p in stage.Traverse():
        if p.GetName() == name and p.HasAPI(UsdPhysics.RigidBodyAPI):
            found = p; break
    assert found, f"no rigid body for link {name}"
    m = UsdPhysics.MassAPI(found)
    mass = m.GetMassAttr().Get()
    rb_count += 1
print("RigidBodyAPI links:", rb_count, "/", len(link_names))

# 3) joints cross-check
axis_map = {UsdPhysics.Tokens.x: (1,0,0), UsdPhysics.Tokens.y: (0,1,0), UsdPhysics.Tokens.z: (0,0,1)}
joint_prims = [p for p in stage.Traverse() if "Joint" in str(p.GetTypeName())]
print("RevoluteJoint prims:", len(joint_prims), "/ expected", len(kin["joints"]))
ok = 0
for j in kin["joints"]:
    p = None
    for cand in stage.Traverse():
        if cand.GetName() == j["name"] and "Joint" in str(cand.GetTypeName()):
            p = cand; break
    assert p, f"missing joint {j['name']}"
    rj = UsdPhysics.RevoluteJoint(p)
    b0 = rj.GetBody0Rel().GetTargets()[0].name
    b1 = rj.GetBody1Rel().GetTargets()[0].name
    axis = axis_map[rj.GetAxisAttr().Get()]
    lo = math.degrees(rj.GetLowerLimitAttr().Get())
    hi = math.degrees(rj.GetUpperLimitAttr().Get())
    lp0 = rj.GetLocalPos0Attr().Get()
    lp1 = rj.GetLocalPos1Attr().Get()
    drv = UsdPhysics.DriveAPI(p, "angular")
    kp = drv.GetStiffnessAttr().Get(); kv = drv.GetDampingAttr().Get()
    mf = drv.GetMaxForceAttr().Get(); typ = drv.GetTypeAttr().Get()
    assert b0 == j["parent"], (j["name"], b0)
    assert b1 == j["child"], (j["name"], b1)
    assert tuple(axis) == tuple(j["axis"]), (j["name"], axis)
    assert abs(lo - j["limit_deg"][0]) < 1e-4, (j["name"], lo)
    assert abs(hi - j["limit_deg"][1]) < 1e-4, (j["name"], hi)
    assert tuple(round(v, 6) for v in lp1) == (0.0, 0.0, 0.0)
    assert abs(mf - j["effort_nm"]) < 1e-5
    print(f"  OK {j['name']:14s} {b0:10s}->{b1:10s} axis={axis} lim=[{lo:7.2f},{hi:7.2f}]deg kp={kp} kv={kv} maxF={mf} type={typ} localPos0={tuple(round(v,4) for v in lp0)}")
    ok += 1
print(f"JOINT CROSS-CHECK: {ok}/{len(kin['joints'])}")

# 4) collision meshes + sole
col = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)]
print("CollisionAPI prims:", len(col), "(11 hulls + 2 soles = 13)")
sole = [p.GetPath().pathString for p in col if p.GetName() == "sole_contact"]
print("sole contact cubes:", sole)

# 5) visual meshes count
meshes = [p for p in stage.Traverse() if p.GetTypeName() == "Mesh"]
print("Mesh prims:", len(meshes), "(11 visual + 11 collision = 22)")

# 6) re-open check already passed; file info
import os, datetime
st = os.stat(OUT)
print("FILE:", OUT, st.st_size, "bytes, mtime", datetime.datetime.fromtimestamp(st.st_mtime).isoformat())
assert rb_count == 11 and len(joint_prims) == 10 and ok == 10 and has_art
print("ALL ASSERTIONS PASSED")
