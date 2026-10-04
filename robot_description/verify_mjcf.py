#!/usr/bin/env python3
"""verify_mjcf.py - load mjcf/lafengparrot.xml in mujoco and run the mandatory checks."""
import json
import math
import os

import mujoco
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
XML = os.path.join(HERE, "mjcf", "lafengparrot.xml")
KIN = os.path.join(HERE, "kinematics.json")

deg2rad = math.pi / 180.0


def main():
    with open(KIN, "r", encoding="utf-8") as fh:
        kin = json.load(fh)

    model = mujoco.MjModel.from_xml_path(XML)
    data = mujoco.MjData(model)

    print("=" * 64)
    print("model loaded from:", XML)
    print("nq=%d  nv=%d  nu=%d  (expected nv=16, nu=10; nq=17 = 7 freebase + 10 hinge)"
          % (model.nq, model.nv, model.nu))

    assert model.nv == 16, "nv != 16"
    assert model.nu == 10, "nu != 10"
    # NOTE: task brief expected nq==16, but a MuJoCo freejoint uses a quaternion
    # (7 qpos: 3 trans + 4 quat), so nq = 7 + 10 = 17. This is correct & standard.

    # ---- actuators ----
    print("-" * 64)
    print("actuators (%d):" % model.nu)
    act_joints = []
    for i in range(model.nu):
        jid = model.actuator_trnid[i, 0]
        jname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid)
        aname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i)
        cr = model.actuator_ctrlrange[i]
        act_joints.append(jname)
        print("  [%2d] act=%-16s -> joint=%-14s ctrlrange=[%.3f, %.3f] rad"
              % (i, aname, jname, cr[0], cr[1]))

    # ---- joint range cross-check (deg -> rad) ----
    print("-" * 64)
    print("joint range cross-check vs kinematics.json (tol=1e-6 rad):")
    jid_of = {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i): i for i in range(model.njnt)}
    ok = 0
    for j in kin["joints"]:
        i = jid_of[j["name"]]
        got = model.jnt_range[i]
        exp = np.array(j["limit_deg"]) * deg2rad
        match = np.allclose(got, exp, atol=1e-6)
        ok += bool(match)
        print("  %-14s range=[%8.3f,%8.3f] rad  expected=[%8.3f,%8.3f] rad  %s"
              % (j["name"], got[0], got[1], exp[0], exp[1], "OK" if match else "MISMATCH"))
    print("  -> %d/%d joints match" % (ok, len(kin["joints"])))

    # ---- FK check at qpos0 (trunk at origin, all joints 0) ----
    print("-" * 64)
    mujoco.mj_forward(model, data)
    shin_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "shin_L")
    sole_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "shin_L_sole")
    trunk_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk")
    print("FK at qpos0 (trunk z=0, all joints=0):")
    print("  trunk xpos z   = %.4f m (expect 0.0)" % data.xpos[trunk_id, 2])
    print("  shin_L xpos z  = %.4f m (expect -0.084)" % data.xpos[shin_id, 2])
    print("  centre sole xpos z= %.4f m (expect -0.1365)" % data.geom_xpos[sole_id, 2])

    # ---- simulation: lift base so soles rest on plane, then step 400 ----
    # Rocker centre-facet bottom = shin(-0.084) + local(-0.054) = -0.138.
    # Lift freebase z by +0.138 so the zero-pose soles just touch z=0.
    data2 = mujoco.MjData(model)
    data2.qpos[2] = 0.138
    mujoco.mj_forward(model, data2)
    z0 = data2.qpos[2]
    print("-" * 64)
    print("sim: lifted freebase z=%.3f so soles touch plane; stepping 400 x 0.002s = 0.8s" % z0)
    nstep = 400
    try:
        for _ in range(nstep):
            mujoco.mj_step(model, data2)
        err = None
    except Exception as e:  # noqa
        err = repr(e)
    print("  step exception:", err)
    finite = bool(np.all(np.isfinite(data2.qpos)) and np.all(np.isfinite(data2.qvel)))
    print("  finite qpos/qvel:", finite)
    print("  trunk z start=%.4f m -> end=%.4f m" % (z0, data2.qpos[2]))
    print("  contact pairs (ncon) at end:", data2.ncon)
    # nonzero MuJoCo warnings
    warned = []
    for code in range(int(mujoco.mjtWarning.mjNWARNING)):
        cnt = int(data2.warning[code].number)
        if cnt:
            warned.append((mujoco.mjtWarning(code).name, cnt))
    print("  mujoco warnings:", warned if warned else "none")
    print("=" * 64)


if __name__ == "__main__":
    main()
