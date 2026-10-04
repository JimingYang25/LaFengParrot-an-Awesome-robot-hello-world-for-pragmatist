"""Part registry — auto-discovers every builder module in source/lib and source/frame.

Each module must expose META (dict) and build(cfg=None) (CONVENTIONS §3).
Agents add files to those directories; this registry picks them up with no
merge conflicts (import via importlib, namespace-qualified part ids).
"""
import importlib
import importlib.util
import pathlib
import sys

CAD_ROOT = pathlib.Path(__file__).resolve().parents[1]  # .../CAD
SOURCE = CAD_ROOT / "source"

_LIB_DIR = SOURCE / "lib"
_FRAME_DIR = SOURCE / "frame"

_CACHE = None


def _iter_modules(directory):
    for p in sorted(directory.glob("*.py")):
        if p.name.startswith("_"):
            continue
        yield p.stem, p


def _load(directory):
    out = {}
    for stem, path in _iter_modules(directory):
        spec = importlib.util.spec_from_file_location(f"lafp_{stem}", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        meta = getattr(mod, "META", None)
        build = getattr(mod, "build", None)
        if meta and callable(build):
            out[meta["part_id"]] = {"meta": meta, "build": build, "module": mod}
    return out


def all_parts(refresh=False):
    """dict[part_id] -> {"meta": META, "build": callable, "module": mod}."""
    global _CACHE
    if _CACHE is None or refresh:
        lib = _load(_LIB_DIR)
        frame = _load(_FRAME_DIR)
        _CACHE = {**lib, **frame}
    return _CACHE


def part(part_id):
    return all_parts()[part_id]
