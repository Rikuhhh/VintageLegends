# src/save_manager.py
import json
import base64
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
            # penetration base stat
            "base_penetration": getattr(player, 'base_penetration', getattr(player, 'penetration', 0.0)),
            # agility base stat
            "base_agility": getattr(player, 'base_agility', getattr(player, 'agility', 0)),
            # canonical base max HP
            "base_max_hp": getattr(player, 'base_max_hp', getattr(player, 'max_hp', 100)),
            # mana stats
            "current_mana": getattr(player, 'current_mana', 0),
            "base_max_mana": getattr(player, 'base_max_mana', 0),
            "base_mana_regen": getattr(player, 'base_mana_regen', 0),
            "base_magic_power": getattr(player, 'base_magic_power', 0),
            "base_magic_penetration": getattr(player, 'base_magic_penetration', 0),
            # skills
            "skills": getattr(player, 'skills', []),
            "equipped_skills": getattr(player, 'equipped_skills', []),
            "skill_cooldowns": getattr(player, 'skill_cooldowns', {}),
            # unspent skill points
            "unspent_points": getattr(player, 'unspent_points', 0),
            "gold": player.gold,
            "xp": player.xp,
            "level": player.level,
            "inventory": player.inventory,
            "equipment": player.equipment,
            "highest_wave": max(getattr(player, 'highest_wave', 0), getattr(battle, 'wave', 0) if battle else 0),
            # challenge progression
            "challenge_coins": getattr(player, 'challenge_coins', 0),
            "permanent_upgrades": getattr(player, 'permanent_upgrades', {}),
            # selected character id (if the game uses character chooser)
            "selected_character": getattr(player, 'selected_character', None),
            # Game seed and shop statistics
            "game_seed": getattr(player, 'game_seed', None),
            "total_items_bought": getattr(player, 'total_items_bought', 0),
            "total_gold_spent": getattr(player, 'total_gold_spent', 0),
            "cumulative_price_increase": getattr(player, 'cumulative_price_increase', 0.0),
        }
        # include current battle state if provided
        try:
            if battle is not None:
                data['wave'] = getattr(battle, 'wave', 1)
                # save current zone
                current_zone = getattr(battle, 'current_zone', None)
                if current_zone:
                    data['current_zone_id'] = current_zone.get('id')
                # save current enemy HP if there is an active enemy (not in shop)
                if getattr(battle, 'enemy', None) and not getattr(battle, 'in_shop', False):
                    data['enemy_hp'] = getattr(battle.enemy, 'hp', None)
                    data['enemy_id'] = getattr(battle.enemy, 'id', None)
        except Exception:
            pass
        # Encode save data with base64
        json_str = json.dumps(data, indent=4)
        encoded_data = base64.b64encode(json_str.encode('utf-8'))
        with open(self.save_dir / "save.save", "wb") as f:
            f.write(encoded_data)
        print("💾 Sauvegarde réussie.")

    def load(self):
        path = self.save_dir / "save.save"
        if path.exists():
            try:
                with open(path, "rb") as f:
                    encoded_data = f.read()
                    decoded_data = base64.b64decode(encoded_data)
                    data = json.loads(decoded_data.decode('utf-8'))
                    print("📂 Sauvegarde chargée.")
                    # Validate critical fields
                    if not isinstance(data, dict):
                        print("⚠️ Invalid save format, starting fresh")
                        return None
                    # Ensure critical numeric fields are valid
                    try:
                        data['hp'] = max(1, int(data.get('hp', 100)))
                        data['max_hp'] = max(1, int(data.get('max_hp', 100)))
                        data['gold'] = max(0, int(data.get('gold', 0)))
                        data['level'] = max(1, int(data.get('level', 1)))
                        # Mana fields
                        data['current_mana'] = max(0, int(data.get('current_mana', 0)))
                        data['base_max_mana'] = max(0, int(data.get('base_max_mana', 0)))
                        # Skills
                        if 'skills' not in data:
                            data['skills'] = []
                        if 'equipped_skills' not in data:
                            data['equipped_skills'] = []
                        if 'skill_cooldowns' not in data:
                            data['skill_cooldowns'] = {}
                    except (ValueError, TypeError):
                        print("⚠️ Corrupted save data, starting fresh")
                        return None
                    return data
            except json.JSONDecodeError:
                print("⚠️ Save file corrupted, starting fresh")
                return None
            except Exception as e:
                print(f"⚠️ Error loading save: {e}, starting fresh")
                return None
        return None

