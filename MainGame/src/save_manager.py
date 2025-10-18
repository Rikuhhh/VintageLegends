# src/save_manager.py
import json
from pathlib import Path

class SaveManager:
    def __init__(self, save_dir):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def save(self, player, battle=None):
        data = {
            "name": player.name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            # save base stats (not transient equipped-modified stats)
            "base_atk": getattr(player, 'base_atk', getattr(player, 'atk', 0)),
            "base_defense": getattr(player, 'base_defense', getattr(player, 'defense', 0)),
            # critical base stats
            "base_critchance": getattr(player, 'base_critchance', getattr(player, 'critchance', 0.0)),
            "base_critdamage": getattr(player, 'base_critdamage', getattr(player, 'critdamage', 1.5)),
            # canonical base max HP
            "base_max_hp": getattr(player, 'base_max_hp', getattr(player, 'max_hp', 100)),
            # unspent skill points
            "unspent_points": getattr(player, 'unspent_points', 0),
            "gold": player.gold,
            "xp": player.xp,
            "level": player.level,
            "inventory": player.inventory,
            "equipment": player.equipment,
            "highest_wave": getattr(player, 'highest_wave', 0),
            # challenge progression
            "challenge_coins": getattr(player, 'challenge_coins', 0),
            "permanent_upgrades": getattr(player, 'permanent_upgrades', {}),
            # selected character id (if the game uses character chooser)
            "selected_character": getattr(player, 'selected_character', None),
        }
        # include current battle state if provided
        try:
            if battle is not None:
                data['wave'] = getattr(battle, 'wave', None)
                # save current enemy HP if there is an active enemy
                if getattr(battle, 'enemy', None):
                    data['enemy_hp'] = getattr(battle.enemy, 'hp', None)
                    data['enemy_id'] = getattr(battle.enemy, 'id', None)
        except Exception:
            pass
        with open(self.save_dir / "save.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("💾 Sauvegarde réussie.")

    def load(self):
        path = self.save_dir / "save.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                print("📂 Sauvegarde chargée.")
                data = json.load(f)
                # return full data to caller
                return data
        return None
