#!/usr/bin/env python3
"""make_mjcf.py - generate the primary MuJoCo (MJCF) PPO asset for LaFengParrot.

Single frozen source:
  kinematics.json  (11 links, 10 revolute joints, limits, actuator/contact/sim opts)
  inertials.json   (per-link mass / com / inertia; includes the 105 g build lump)
  meshes/visual/<link>.stl  +  meshes/collision/<link>_col.stl   (units = mm)

Tree: NESTED serial chain (trunk -> hip_roll -> hip_pitch -> knee -> shin+foot).
Output: mjcf/lafengparrot.xml  (all lowercase filename).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
KIN_PATH = os.path.join(HERE, "kinematics.json")
INER_PATH = os.path.join(HERE, "inertials.json")
OUT_PATH = os.path.join(HERE, "mjcf", "lafengparrot.xml")

MM = 0.001  # STLs authored in mm -> MuJoCo wants m


def f6(x):
    return "%.6g" % float(x)


def load():
    with open(KIN_PATH, "r", encoding="utf-8") as fh:
        kin = json.load(fh)
    with open(INER_PATH, "r", encoding="utf-8") as fh:
        iner = json.load(fh)
    return kin, iner


def armature_for(jname):
    """leg joints 0.01, wing/neck joints 0.002 (kinematics.json actuators)."""
    if jname.startswith(("hip_", "knee_")):
        return 0.01
    return 0.002  # wing_flap_*, neck_yaw, neck_pitch


def rocker_facet_box(p0, p1, half_thickness):
    """Return (pos_x, pos_z, half_length, pitch_deg) for one underside facet.

    p0/p1 describe the desired lower contact surface in the shin X-Z plane.
    A thin rotated box is placed above that surface.  Using finite facets keeps
    neutral standing numerically stable, unlike a cylinder's line contact.
    """
    x0, z0 = map(float, p0)
    x1, z1 = map(float, p1)
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    pitch = -math.atan2(dz, dx)

    bottom_x = 0.5 * (x0 + x1)
    bottom_z = 0.5 * (z0 + z1)
    # bottom midpoint = centre + R_y(pitch) * (0, 0, -half_thickness)
    centre_x = bottom_x + half_thickness * math.sin(pitch)
    centre_z = bottom_z + half_thickness * math.cos(pitch)
    return centre_x, centre_z, 0.5 * length, math.degrees(pitch)


def build(kin, iner):
    joints = kin["joints"]
    link_in = iner["links"]

    # child name -> joint record
    jchild = {j["child"]: j for j in joints}
    # parent name -> list of child names (order preserved from joints list)
    children = {}
    for j in joints:
        children.setdefault(j["parent"], []).append(j["child"])

    # frame origin of each link, mm, expressed in trunk/world frame
    origin_mm = {name: link_in[name]["frame_origin_mm"] for name in link_in}

    lines = []
    a = lines.append

    a('<mujoco model="lafengparrot">')
    a('  <compiler angle="degree" coordinate="local" eulerseq="xyz" meshdir="../meshes/visual"/>')
    so = kin["sim_options"]
    a('  <option timestep="%s" gravity="%g %g %g"/>'
      % (f6(so["timestep_s"]), so["gravity"][0], so["gravity"][1], so["gravity"][2]))
    a('')
    a('  <default class="main">')
    a('    <geom type="mesh" contype="0" conaffinity="0"/>')
    a('    <joint damping="0.5" frictionloss="0.05"/>')
    a('  </default>')
    a('')

    # ---- asset: meshes (visual from meshdir, collision via ../collision/) ----
    a('  <asset>')
    for name in [l["name"] for l in kin["links"]]:
        a('    <mesh name="%s" file="%s.stl" scale="0.001 0.001 0.001"/>' % (name, name))
    for name in [l["name"] for l in kin["links"]]:
        a('    <mesh name="%s_col" file="../collision/%s_col.stl" scale="0.001 0.001 0.001"/>'
          % (name, name))
    a('  </asset>')
    a('')

    # ---- worldbody ----
    a('  <worldbody>')
    a('    <light pos="0 0 3" dir="0 0 -1" diffuse="0.8 0.8 0.8" specular="0.1 0.1 0.1"/>')
    a('    <geom name="floor" type="plane" size="20 20 0.1" contype="1" conaffinity="1"'
      ' rgba="0.8 0.8 0.8 1" friction="1 0.005 0.0001"/>')

    def emit_body(name, indent):
        # NESTED serial chain: each body is a child of its kinematic parent.
        # Body pos = (child frame_origin - parent frame_origin) in meters.
        pad = "  " * indent
        li = link_in[name]
        mass_kg = li["mass_g"] / 1000.0
        com = li["com_m"]
        M = li["inertia_kgm2"]
        ixx, iyy, izz = M[0][0], M[1][1], M[2][2]
        ixy, ixz, iyz = M[0][1], M[0][2], M[1][2]

        if name == "trunk":
            a('%s<body name="trunk" pos="0 0 0">' % pad)
            a('%s  <freejoint/>' % pad)
        else:
            j = jchild[name]
            par = j["parent"]
            rel = [(c - p) * MM for c, p in zip(origin_mm[name], origin_mm[par])]
            a('%s<body name="%s" pos="%s %s %s">' % (pad, name, f6(rel[0]), f6(rel[1]), f6(rel[2])))
            ax = j["axis"]
            lo, hi = j["limit_deg"]
            a('%s  <joint name="%s" type="hinge" axis="%g %g %g" limited="true"'
              ' range="%g %g" armature="%s"/>'
              % (pad, j["name"], ax[0], ax[1], ax[2], lo, hi, f6(armature_for(j["name"]))))

        a('%s  <inertial pos="%s %s %s" mass="%s" fullinertia="%s"/>'
          % (pad, f6(com[0]), f6(com[1]), f6(com[2]), f6(mass_kg),
             " ".join(f6(v) for v in (ixx, iyy, izz, ixy, ixz, iyz))))
        a('%s  <geom name="%s_vis" class="main" type="mesh" mesh="%s"/>' % (pad, name, name))
        a('%s  <geom name="%s_col" class="main" type="mesh" mesh="%s_col"/>' % (pad, name, name))

        if name == "trunk":
            site = kin["sites"]["imu_trunk"]["pos"]
            a('%s  <site name="imu_trunk" pos="%g %g %g" size="0.01" rgba="1 0 0 1"/>'
              % (pad, site[0] * MM, site[1] * MM, site[2] * MM))

        if name in ("shin_L", "shin_R"):
            sole = kin["contact"]["sole"]
            fr = sole["friction"]
            width = float(sole["width_half_m"])
            half_t = float(sole["contact_half_thickness_m"])
            profile = sole["profile_xz_m"]
            labels = sole["facet_names"]
            for idx, (p0, p1, label) in enumerate(zip(profile[:-1], profile[1:], labels)):
                px, pz, half_len, pitch_deg = rocker_facet_box(p0, p1, half_t)
                # Preserve the legacy centre-sole name used by the gait env.
                gname = "%s_sole" % name if label == "center" else "%s_sole_%s" % (name, label)
                a('%s  <geom name="%s" type="box" size="%s %s %s" pos="%s 0 %s"'
                  ' euler="0 %s 0" contype="1" conaffinity="1" friction="%s %s %s"'
                  ' rgba="0.2 0.2 0.9 1"/>'
                  % (pad, gname, f6(half_len), f6(width), f6(half_t),
                     f6(px), f6(pz), f6(pitch_deg),
                     f6(fr[0]), f6(fr[1]), f6(fr[2])))

        for ch in children.get(name, []):
            emit_body(ch, indent + 1)
        a('%s</body>' % pad)

    a('    <!-- qpos order is MuJoCo DFS = leg-major (hip_roll_L, hip_pitch_L, knee_L, hip_roll_R, ...); actuator order (ctrl vector) is the canonical kinematics.json order; the RL wrapper maps state/action by joint NAME -->')
    emit_body("trunk", 2)
    a('  </worldbody>')
    a('')

    # ---- actuators (canonical kinematics.json joint order; bind by joint name) ----
    # NOTE: with compiler angle="degree", MuJoCo converts <joint range> to radians
    # internally, but a <position> actuator's ctrl target is consumed in RADIANS.
    # Empirically: ctrl=0.384 rad settles the joint at exactly 22 deg (stable),
    # while ctrl=22 blows up. So ctrlrange is in radians to match ctrl.
    a('  <actuator>')
    for j in joints:
        lo, hi = j["limit_deg"]
        effort = float(j["effort_nm"])

        a('    <position name="%s" joint="%s" kp="40" kv="4"'
          ' ctrlrange="%.6g %.6g"'
          ' forcelimited="true" forcerange="%s %s"/>'
          % (
              j["name"],
              j["name"],
              math.radians(lo),
              math.radians(hi),
              f6(-effort),
              f6(effort),
          ))

    a('  </actuator>')
    a('</mujoco>')

    return "\n".join(lines) + "\n"


def main():
    kin, iner = load()
    xml = build(kin, iner)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print("wrote", OUT_PATH, "(%d bytes)" % len(xml))


if __name__ == "__main__":
    main()
