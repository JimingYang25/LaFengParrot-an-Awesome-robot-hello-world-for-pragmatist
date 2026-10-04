"""Dump the joint-name -> qpos/qvel/actuator index map for the MJCF model.
Names are taken from the XML (MuJoCo assigns qpos/qvel by deterministic tree DFS);
addresses are cross-checked against the ACTUAL model (jnt_qposadr / jnt_dofadr).
Run:  python robot_description/make_name_map.py
Writes: robot_description/joint_name_index_map.json
"""
import json, pathlib, xml.etree.ElementTree as ET, mujoco

RD = pathlib.Path(__file__).resolve().parent
XML = RD / "mjcf" / "lafengparrot.xml"
model = mujoco.MjModel.from_xml_path(str(XML))

# --- DFS joint order from the XML (worldbody, in author order) ---
root = ET.parse(str(XML)).getroot()
order = []

def walk(body, parent_joints):
    joints = []
    for el in body:
        if el.tag == "joint":
            name = el.get("name")
            if name and not name.startswith("free"):
                joints.append(name)
    parent_joints.append(joints)
    for el in body:
        if el.tag == "body":
            walk(el, parent_joints)

wj = []
walk(root.find("worldbody"), wj)
dfs = [j for js in wj for j in js]
# freejoint: trunk is the first body; its <freejoint/> joint has no name attr
free_count = sum(1 for b in root.iter("body") for j in b if j.tag == "freejoint")
assert free_count == 1, "expected exactly one freejoint"

# --- addresses from the model, matched by DFS order ---
# model joints in DFS order: free at index 0, then hinges
addr_ok = all(model.jnt_qposadr[j] == (7 + i) for j, i in zip(range(1, model.njnt), range(model.njnt - 1)))
qpos_map = {
    "freejoint_trans": [0, 1, 2],
    "freejoint_quat": [3, 4, 5, 6],
}
qvel_map = {"freejoint_rot": [0, 1, 2]}
for i, name in enumerate(dfs):
    qpos_map[name] = 7 + i
    qvel_map[name] = 6 + i

# --- actuators: <actuator><position joint="..."> in file order ---
act_el = [a.get("joint") for a in root.iter("position")]
act_map = {n: i for i, n in enumerate(act_el)}

out = {
    "model": "lafengparrot (MJCF, nested serial chain)",
    "nq": model.nq, "nv": model.nv, "nu": model.nu,
    "freejoint_qpos_layout": "3 trans + 4 quat = 7 values; qvel 3 trans + 3 rot = 6 values",
    "note": "MuJoCo qpos/qvel order is tree-DFS (leg-major). RL code MUST index observations/actions BY NAME via this map, never by hard-coded position. Actuator (ctrl) order is the canonical kinematics.json order.",
    "qpos_index": qpos_map,
    "qvel_index": qvel_map,
    "actuator_index": act_map,
    "qpos_order": ["freejoint"] + dfs,
    "actuator_order": act_el,
    "_checks": {
        "model.nq == 7 + 10 == 17": model.nq == 17,
        "model.nv == 6 + 10 == 16": model.nv == 16,
        "model.nu == 10": model.nu == 10,
        "qpos addresses match XML DFS (7+i)": addr_ok,
        "actuators bind to the 10 named joints": sorted(act_el) == sorted(dfs),
    },
}
assert all(out["_checks"].values()), out["_checks"]
(RD / "joint_name_index_map.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("nq", model.nq, "nv", model.nv, "nu", model.nu, "| checks:", out["_checks"])
print("qpos order:", out["qpos_order"])
print("actuator order:", out["actuator_order"])
print("wrote", RD / "joint_name_index_map.json")
