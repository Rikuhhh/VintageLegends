# src/player.py
from pathlib import Path
import json


class Player:
    def __init__(self, data):
        self.name = data.get("name", "Inconnu")
        self.max_hp = data.get("hp", 100)
        self.hp = self.max_hp
        # keep base stats separately so equipment application is idempotent
        self.base_atk = data.get("atk", 10)
        self.base_defense = data.get("def", 5)
        self.atk = self.base_atk
        self.defense = self.base_defense
        # critical stats: base values (base_critchance stored as probability 0.0-1.0)
        self.base_critchance = float(data.get('critchance', 0.0))
        self.base_critdamage = float(data.get('critdamage', 1.5))
        # current effective crit stats (after equipment)
        self.critchance = self.base_critchance
        self.critdamage = self.base_critdamage
        self.gold = 0
        self.xp = 0
        self.level = 1
        # Challenge progression (persistent)
        self.challenge_coins = int(data.get('challenge_coins', 0))
        # dict of upgrade_id -> level
        self.permanent_upgrades = data.get('permanent_upgrades', {})
        # Points non dépensés à attribuer lors d'un level-up
        self.unspent_points = 0
        # Inventaire simple: dict of item_id -> count
        self.inventory = {}
        # Equipment slots store item ids
        self.equipment = {
            "weapon": None,
            "armor": None,
        }

    def take_damage(self, dmg):
        dmg_taken = max(1, dmg - self.defense)
        self.hp = max(0, self.hp - dmg_taken)
        return dmg_taken

    def gain_xp(self, amount):
        self.xp += amount
        # Supporte plusieurs niveaux d'un coup
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level_up()

    def level_up(self):
        self.level += 1
        # Accorde un boost de vie de base et soigne le joueur
        self.max_hp += 10
        self.hp = self.max_hp
        # Accord de points de compétence à dépenser manuellement (via l'UI)
        self.unspent_points += 3
        print(f"{self.name} est maintenant niveau {self.level} ! (+3 points non dépensés)")

    def spend_point(self, stat: str) -> bool:
        """Dépense un point sur une statistique: 'atk', 'def', 'hp'. Retourne True si succès."""
        if self.unspent_points <= 0:
            return False
        if stat == "atk":
            self.base_atk += 1
        elif stat == "def":
            self.base_defense += 1
        elif stat == "hp":
            self.max_hp += 5
            self.hp += 5
        else:
            return False

        self.unspent_points -= 1
        print(f"{self.name} dépense 1 point sur {stat}. Points restants: {self.unspent_points}")
        # recalc current stats after base change
        self._recalc_stats()
        return True

    def add_item(self, item: dict, auto_equip: bool = True):
        """Add an item to the player.

        Behavior:
        - If auto_equip is False: just add to inventory (no equip).
        - If auto_equip is True and the item is equippable (weapon/armor):
            * If the same item is already equipped: increment inventory (it's a spare copy).
            * Otherwise equip the new item and return the previous equipped item to inventory (if any).
        - Non-equippable items are always added to inventory.

        This avoids the previous duplicate behavior where the new equipped item stayed in inventory
        while also being marked as equipped.
        """
        item_id = item.get("id")
        if not item_id:
            return

        itype = item.get("type")

        # If we shouldn't auto-equip, simply add to inventory and return
        if not auto_equip:
            self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
            return

        # Auto-equip enabled: handle equippable types specially
        if itype == "weapon" and item.get("attack"):
            prev_id = self.equipment.get("weapon")
            # If same item already equipped, treat as spare and add to inventory
            if prev_id == item_id:
                self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
                return
            # Equip the new item and return previous to inventory (if any)
            if prev_id:
                self.inventory[prev_id] = self.inventory.get(prev_id, 0) + 1
            self.equipment["weapon"] = item_id
            self._recalc_stats()
            return

        if itype == "armor" and item.get("defense"):
            prev_id = self.equipment.get("armor")
            if prev_id == item_id:
                self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
                return
            if prev_id:
                self.inventory[prev_id] = self.inventory.get(prev_id, 0) + 1
            self.equipment["armor"] = item_id
            self._recalc_stats()
            return

        # Fallback: non-equip items or items without stats -> go to inventory
        self.inventory[item_id] = self.inventory.get(item_id, 0) + 1

    def equip_item_by_id(self, item_id: str) -> bool:
        """Equip an item by id from the item's definitions without changing inventory counts."""
        item = self._load_item_by_id(item_id)
        if not item:
            return False
        itype = item.get('type')
        if itype == 'weapon' and item.get('attack'):
            prev_id = self.equipment.get('weapon')
            if prev_id == item_id:
                return False
            # return previous weapon to inventory
            if prev_id:
                self.inventory[prev_id] = self.inventory.get(prev_id, 0) + 1
            self.equipment['weapon'] = item_id
            self._recalc_stats()
            return True
        if itype == 'armor' and item.get('defense'):
            prev_id = self.equipment.get('armor')
            if prev_id == item_id:
                return False
            if prev_id:
                self.inventory[prev_id] = self.inventory.get(prev_id, 0) + 1
            self.equipment['armor'] = item_id
            self._recalc_stats()
            return True
        return False

    def remove_item(self, item_id: str, qty: int = 1) -> bool:
        """Remove qty of item_id from inventory. Returns True if removed."""
        if self.inventory.get(item_id, 0) >= qty:
            self.inventory[item_id] -= qty
            if self.inventory[item_id] <= 0:
                del self.inventory[item_id]
            return True
        return False

    def _load_item_by_id(self, item_id: str):
        """Load item definition from data/items.json by id. Returns dict or None."""
        try:
            base = Path(__file__).resolve().parents[1]
            items_path = base / 'data' / 'items.json'
            if items_path.exists():
                with open(items_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for it in data.get('items', []):
                        if it.get('id') == item_id:
                            return it
        except Exception:
            return None
        return None

    def has_item(self, item_id: str) -> bool:
        return self.inventory.get(item_id, 0) > 0

    def _recalc_stats(self):
        """Recalculate current atk/def based on base stats and equipped items."""
        # start from base
        self.atk = getattr(self, 'base_atk', 0)
        self.defense = getattr(self, 'base_defense', 0)
        # reset crit stats to base
        self.critchance = getattr(self, 'base_critchance', 0.0)
        self.critdamage = getattr(self, 'base_critdamage', 1.5)
        # weapon bonus
        wid = self.equipment.get('weapon')
        if wid:
            w = self._load_item_by_id(wid)
            if w and w.get('attack'):
                self.atk += w.get('attack', 0)
            # weapon may also add crit stats
            if w and w.get('critchance'):
                try:
                    self.critchance += float(w.get('critchance', 0.0))
                except Exception:
                    pass
            if w and w.get('critdamage'):
                try:
                    self.critdamage += float(w.get('critdamage', 0.0))
                except Exception:
                    pass
        # armor bonus
        aid = self.equipment.get('armor')
        if aid:
            a = self._load_item_by_id(aid)
            if a and a.get('defense'):
                self.defense += a.get('defense', 0)
            # armor may also add crit stats
            if a and a.get('critchance'):
                try:
                    self.critchance += float(a.get('critchance', 0.0))
                except Exception:
                    pass
            if a and a.get('critdamage'):
                try:
                    self.critdamage += float(a.get('critdamage', 0.0))
                except Exception:
                    pass

        # Apply permanent upgrades (data-driven). Load definitions from data/upgrades.json if present.
        try:
            base = Path(__file__).resolve().parents[1]
            up_path = base / 'data' / 'upgrades.json'
            if up_path.exists():
                with open(up_path, 'r', encoding='utf-8') as f:
                    import json
                    udata = json.load(f)
                    defs = {u.get('id'): u for u in udata.get('upgrades', [])}
                    for uid, lvl in (self.permanent_upgrades or {}).items():
                        u = defs.get(uid)
                        if not u or lvl <= 0:
                            continue
                        eff = u.get('effect', {})
                        etype = eff.get('type')
                        stat = eff.get('stat')
                        val = eff.get('value', 0)
                        try:
                            if etype == 'add':
                                # apply additive effect per level
                                setattr(self, stat, getattr(self, stat, 0) + val * int(lvl))
                        except Exception:
                            pass
        except Exception:
            pass

    def unequip(self, slot: str) -> bool:
        """Unequip item in slot ('weapon' or 'armor') and remove its stat bonuses."""
        if slot not in self.equipment:
            return False
        iid = self.equipment.get(slot)
        if not iid:
            return False
        item = self._load_item_by_id(iid)
        if not item:
            # still remove equipment reference
            self.equipment[slot] = None
            return True

        # remove equipment reference and recalc stats (idempotent)
        self.equipment[slot] = None
        # return the unequipped item back to inventory
        self.inventory[iid] = self.inventory.get(iid, 0) + 1
        self._recalc_stats()
        return True

    def is_dead(self):
        return self.hp <= 0
