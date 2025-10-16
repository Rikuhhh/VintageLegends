# src/save_manager.py
import json
from pathlib import Path

class SaveManager:
    def __init__(self, save_dir):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def save(self, player):
        data = {
            "name": player.name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "atk": player.atk,
            "defense": player.defense,
            "gold": player.gold,
            "xp": player.xp,
            "level": player.level
        }
        with open(self.save_dir / "save.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("💾 Sauvegarde réussie.")

    def load(self):
        path = self.save_dir / "save.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                print("📂 Sauvegarde chargée.")
                return json.load(f)
        return None
