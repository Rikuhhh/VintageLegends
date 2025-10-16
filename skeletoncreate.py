"""
game_project_structure.py
Ce script montre l'organisation complète du projet de jeu tour par tour.
Tu peux le lancer pour créer automatiquement tous les dossiers et fichiers de base.
"""

from pathlib import Path
import json

# Dossier racine du projet
ROOT = Path(__file__).parent / "MainGame"

# Arborescence du projet
structure = {
    "assets": {
        "images": {
            "backgrounds": {},
            "characters": {},
            "monsters": {},
            "ui": {}
        },
        "sounds": {
            "music": {},
            "effects": {}
        }
    },
    "data": {
        "monsters.json": None,
        "attacks.json": None,
        "items.json": None,
        "settings.json": None,
        "skill_trees.json": None
    },
    "saves": {},
    "src": {
        "main.py": None,
        "battle_system.py": None,
        "ui_manager.py": None,
        "player.py": None,
        "enemy.py": None,
        "shop.py": None,
        "level_system.py": None,
        "save_manager.py": None
    },
    "README.md": None
}

# Fonction pour créer récursivement la structure
def create_structure(base, struct):
    for name, content in struct.items():
        path = base / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_structure(path, content)
        else:
            path.touch(exist_ok=True)

# Créer la structure
create_structure(ROOT, structure)

# Exemple de contenu minimal pour settings.json
default_settings = {
    "fullscreen": False,
    "resolution": [1280, 720],
    "volume": {
        "music": 0.8,
        "effects": 0.8
    },
    "language": "fr"
}

settings_path = ROOT / "data" / "settings.json"
if settings_path.stat().st_size == 0:  # Si vide
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(default_settings, f, indent=4, ensure_ascii=False)

print(f"✅ Structure du projet créée dans : {ROOT.resolve()}")
