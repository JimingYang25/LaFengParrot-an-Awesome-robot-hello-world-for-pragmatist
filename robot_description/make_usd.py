#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_usd.py  (LaFengParrot / REV-B 2026-09-27)

Build usd/lafengparrot.usd for Isaac-Sim / Lab import from the SINGLE frozen
source: kinematics.json + inertials.json + meshes/{visual,collision}/*.stl.

Physics baked with pxr.UsdPhysics (usd-core 26.8, cp314 win_amd64):
  - ArticulationRootAPI  on /LafengParrot
  - RigidBodyAPI + MassAPI (mass / CoM / principal-axis inertia) on every link
  - RevoluteJoint (body0/body1, localPos0 = joint origin in PARENT frame [m],
    localPos1 = (0,0,0)) with lower/upper limits [rad]
  - DriveAPI angular, type="force", kp=40, kv=4 (single set; = actuators.defaults),
    maxForce = effort_nm from kinematics.json
  - CollisionAPI on collision-hull meshes + the sole contact cube on shin_L/R

Units: meters / kg / rad. STL meshes authored in mm -> x0.001.
"""
import importlib.util as _ilu  # noqa: F401  (explicit, per project convention)
import json
import math
import os
import sys

import numpy as np
import trimesh

from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf, Vt

HERE = os.path.dirname(os.path.abspath(__file__))
KIN_PATH   = os.path.join(HERE, "kinematics.json")
INER_PATH  = os.path.join(HERE, "inertials.json")
VIS_DIR    = os.path.join(HERE, "meshes", "visual")
COL_DIR    = os.path.join(HERE, "meshes", "collision")
OUT_PATH   = os.path.join(HERE, "usd", "lafengparrot.usd")

MM = 0.001
KP_DEFAULT = 40.0   # [EST] actuators.defaults.kp
KV_DEFAULT = 4.0    # [EST] actuators.defaults.kv


def deg2rad(d):
    return d * math.pi / 180.0


def load_stl_mesh(path):
    m = trimesh.load(path, force="mesh", process=False)
    verts = np.asarray(m.vertices, dtype=np.float64) * MM
    faces = np.asarray(m.faces, dtype=np.int64)
    return verts, faces


def write_mesh(stage, path, verts, faces, with_collision=False):
    mesh = UsdGeom.Mesh.Define(stage, path)
    pts = Vt.Vec3fArray([Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in verts])
    mesh.CreatePointsAttr(pts)
    counts = Vt.IntArray([3] * len(faces))
    mesh.CreateFaceVertexCountsAttr(counts)
    idx = Vt.IntArray(np.ascontiguousarray(faces.reshape(-1)).tolist())
    mesh.CreateFaceVertexIndicesAttr(idx)
    mn = verts.min(axis=0)
    mx = verts.max(axis=0)
    mesh.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(*mn.tolist()), Gf.Vec3f(*mx.tolist())]))
    UsdGeom.Xformable(mesh).CreatePurposeAttr().Set(UsdGeom.Tokens.default_)
    if with_collision:
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    return mesh


def _mat3_to_quat(R):
    """R (3x3, orthonormal, det=+1) -> Gf.Quatf (shepperd)."""
    m00, m11, m22 = R[0, 0], R[1, 1], R[2, 2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    return Gf.Quatf(float(w), float(x), float(y), float(z))


def inertia_to_principal(I):
    """3x3 symmetric inertia (kg m^2) -> (diag[3], Gf.Quatf principal axes)."""
    I = np.asarray(I, dtype=np.float64)
    w, V = np.linalg.eigh(I)
    # eigh returns orthonormal eigenvectors; guard against reflection (det=-1)
    if np.linalg.det(V) < 0:
        V[:, 0] = -V[:, 0]
    return Gf.Vec3f(float(w[0]), float(w[1]), float(w[2])), _mat3_to_quat(V)


def main():
    with open(KIN_PATH, "r", encoding="utf-8") as f:
        kin = json.load(f)
    with open(INER_PATH, "r", encoding="utf-8") as f:
        iner = json.load(f)

    link_names = [l["name"] for l in kin["links"]]
    joints = kin["joints"]
    # global (trunk-frame) origins of each link, meters
    link_origin_m = {l["name"]: [x * MM for x in l["frame_origin"]] for l in kin["links"]}

    stage = Usd.Stage.CreateNew(OUT_PATH)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    root = UsdGeom.Xform.Define(stage, "/LafengParrot")
    stage.SetDefaultPrim(root.GetPrim())
    UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())

    # parent-of-link map from joints (trunk has no parent)
    link_parent = {}
    for j in joints:
        link_parent[j["child"]] = j["parent"]

    # ---- build nested Xform tree for links ---------------------------------
    # child Xform translate = joint origin in parent frame = global_joint - parent_origin
    joint_local0 = {}
    for j in joints:
        p_origin = np.array(link_origin_m[j["parent"]])
        j_origin = np.array([x * MM for x in j["origin"]])
        joint_local0[j["name"]] = (j_origin - p_origin).tolist()

    link_xform = {}
    # trunk first
    trunk_prim = UsdGeom.Xform.Define(stage, "/LafengParrot/trunk")
    UsdGeom.Xformable(trunk_prim).AddTranslateOp().Set(Gf.Vec3d(0, 0, 0))
    link_xform["trunk"] = trunk_prim

    def define_link(link):
        name = link["name"]
        if name == "trunk":
            return trunk_prim
        parent = link_parent[name]
        parent_prim = link_xform[parent]
        path = parent_prim.GetPath().pathString + "/" + name
        xf = UsdGeom.Xform.Define(stage, path)
        # child frame origin sits at the joint axis:
        off = joint_local0[_joint_name_for_child(name)]
        UsdGeom.Xformable(xf).AddTranslateOp().Set(Gf.Vec3d(*[float(x) for x in off]))
        link_xform[name] = xf
        return xf

    def _joint_name_for_child(child):
        for j in joints:
            if j["child"] == child:
                return j["name"]
        raise KeyError(child)

    # order matters: parents before children; kinematics.json already in that order
    for l in kin["links"]:
        if l["name"] == "trunk":
            continue
        define_link(l)

    # ---- physics + mass on every link -------------------------------------
    phys_apis = {"articulation_root": 1, "rigid_body": 0, "mass": 0,
                 "limit": 0, "drive": 0, "collision": 0}
    for name in link_names:
        prim = link_xform[name].GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim); phys_apis["rigid_body"] += 1
        mass_api = UsdPhysics.MassAPI.Apply(prim); phys_apis["mass"] += 1
        info = iner["links"][name]
        mass_api.CreateMassAttr().Set(float(info["mass_g"]) / 1000.0)
        mass_api.CreateCenterOfMassAttr().Set(Gf.Vec3f(*[float(x) for x in info["com_m"]]))
        diag, q = inertia_to_principal(info["inertia_kgm2"])
        mass_api.CreateDiagonalInertiaAttr(diag)
        mass_api.CreatePrincipalAxesAttr(q)

    # ---- meshes: visual + collision hull per link --------------------------
    for name in link_names:
        lx = link_xform[name]
        vpath = lx.GetPath().pathString + "/visual"
        cpath = lx.GetPath().pathString + "/collision"
        UsdGeom.Scope.Define(stage, vpath)
        UsdGeom.Scope.Define(stage, cpath)
        vstl = os.path.join(VIS_DIR, name + ".stl")
        cstl = os.path.join(COL_DIR, name + "_col.stl")
        vv, vf = load_stl_mesh(vstl)
        write_mesh(stage, vpath + "/" + name, vv, vf, with_collision=False)
        cv, cf = load_stl_mesh(cstl)
        write_mesh(stage, cpath + "/" + name + "_col", cv, cf, with_collision=True)
        phys_apis["collision"] += 1

    # ---- sole contact cube on shin_L / shin_R ------------------------------
    for shin in ("shin_L", "shin_R"):
        lx = link_xform[shin]
        cube = UsdGeom.Cube.Define(stage, lx.GetPath().pathString + "/sole_contact")
        UsdGeom.Xformable(cube).AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.054))
        # half-extents [0.020,0.022,0.002] -> full edge = 2*half
        UsdGeom.Xformable(cube).AddScaleOp().Set(Gf.Vec3d(0.040, 0.044, 0.004))
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        phys_apis["collision"] += 1

    # ---- revolute joints ----------------------------------------------------
    axis_token = {(1, 0, 0): UsdPhysics.Tokens.x,
                  (0, 1, 0): UsdPhysics.Tokens.y,
                  (0, 0, 1): UsdPhysics.Tokens.z}
    for j in joints:
        parent_prim = link_xform[j["parent"]]
        joints_scope_path = parent_prim.GetPath().pathString + "/joints"
        if not stage.GetPrimAtPath(joints_scope_path):
            UsdGeom.Scope.Define(stage, joints_scope_path)
        jpath = joints_scope_path + "/" + j["name"]
        rj = UsdPhysics.RevoluteJoint.Define(stage, jpath)
        rj.CreateBody0Rel().SetTargets([link_xform[j["parent"]].GetPath()])
        rj.CreateBody1Rel().SetTargets([link_xform[j["child"]].GetPath()])
        off = joint_local0[j["name"]]
        rj.CreateLocalPos0Attr().Set(Gf.Vec3f(*[float(x) for x in off]))
        rj.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, Gf.Vec3f(0, 0, 0)))
        rj.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))
        rj.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, Gf.Vec3f(0, 0, 0)))
        rj.CreateAxisAttr().Set(axis_token[tuple(j["axis"])])
        lo, hi = deg2rad(j["limit_deg"][0]), deg2rad(j["limit_deg"][1])
        rj.CreateLowerLimitAttr().Set(float(lo))
        rj.CreateUpperLimitAttr().Set(float(hi))
        phys_apis["limit"] += 1
        drive = UsdPhysics.DriveAPI.Apply(rj.GetPrim(), "angular")
        drive.CreateTypeAttr().Set("force")
        drive.CreateStiffnessAttr().Set(KP_DEFAULT)
        drive.CreateDampingAttr().Set(KV_DEFAULT)
        drive.CreateMaxForceAttr().Set(float(j["effort_nm"]))
        phys_apis["drive"] += 1

    stage.GetRootLayer().Save()
    print("WROTE:", OUT_PATH)
    print("PHYSICS APIS BAKED:", json.dumps(phys_apis))


if __name__ == "__main__":
    main()
