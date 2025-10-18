import json
import sys
from pathlib import Path


def resource_path(*parts):
    """Return a Path to a resource bundled with the app.
    Works in normal dev environment and when packaged with PyInstaller (_MEIPASS).
    Usage: resource_path('assets', 'images', 'foo.png') -> Path
    """
    base = getattr(sys, '_MEIPASS', None)
    if base:
        base_path = Path(base)
    else:
        # default to project src parent (MainGame/src)
        base_path = Path(__file__).resolve().parent
    return base_path.joinpath(*parts)


def load_json(name, default=None, data_path=None):
    """Load a JSON file from the data directory.
    - name: filename (e.g. 'gamesettings.json') or absolute path
    - data_path: optional Path or str pointing to data dir
    Returns parsed JSON or default on error.
    """
    if data_path:
        p = Path(data_path) / name
    else:
        # fallback: assume data in a sibling "data" directory to this file's parent
        p = Path(__file__).resolve().parent.parent / 'data' / name
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default or {}
