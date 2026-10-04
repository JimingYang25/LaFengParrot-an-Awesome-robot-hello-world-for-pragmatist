import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
import cadquery as cq
ROOT = HERE.parent.parent
p = ROOT / "exports" / "step" / "LaFengParrot_Standing.STEP"
asm = cq.importers.importStep(str(p))
bb = asm.val().BoundingBox()
print(f"RELOADED standing STEP bbox x[{bb.xmin:.1f},{bb.xmax:.1f}] "
      f"y[{bb.ymin:.1f},{bb.ymax:.1f}] z[{bb.zmin:.1f},{bb.zmax:.1f}]")
print(f"solid count ~ {len(asm.solids().vals()) if hasattr(asm,'solids') else 'n/a'}")
