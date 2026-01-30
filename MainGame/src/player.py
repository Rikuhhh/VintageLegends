# src/player.py
from pathlib import Path
import json


class Player:
    def __init__(self, data):
        # Validate and sanitize input data
        if not isinstance(data, dict):
            data = {}
        
        self.name = str(data.get("name", "Inconnu"))
        # keep a canonical base max HP so upgrades are idempotent
        try:
            self.base_max_hp = max(1, int(data.get("hp", 100)))
        except (ValueError, TypeError):
            self.base_max_hp = 100
        self.max_hp = self.base_max_hp
        self.hp = self.max_hp
        # keep base stats separately so equipment application is idempotent
        try:
            self.base_atk = max(0, int(data.get("atk", 10)))
        except (ValueError, TypeError):
            self.base_atk = 10
        try:
            self.base_defense = max(0, int(data.get("def", 5)))
        except (ValueError, TypeError):
            self.base_defense = 5
        self.atk = self.base_atk
        self.defense = self.base_defense
        # critical stats: base values (base_critchance stored as probability 0.0-1.0)
        try:
            self.base_critchance = max(0.0, min(1.0, float(data.get('critchance', 0.0))))
        except (ValueError, TypeError):
            self.base_critchance = 0.0
        try:
            self.base_critdamage = max(1.0, float(data.get('critdamage', 1.5)))
        except (ValueError, TypeError):
            self.base_critdamage = 1.5
        # current effective crit stats (after equipment)
        self.critchance = self.base_critchance
        self.critdamage = self.base_critdamage
        # Penetration stat (reduces enemy defense effectiveness)
        try:
            self.base_penetration = max(0.0, float(data.get('penetration', 0.0)))
        except (ValueError, TypeError):
            self.base_penetration = 0.0
        self.penetration = self.base_penetration
        # Agility stat (increases crit chance and dodge chance)
        try:
            self.base_agility = max(0, int(data.get('agility', 0)))
        except (ValueError, TypeError):
            self.base_agility = 0
        self.agility = self.base_agility
        # Dodge chance (computed from agility)
        self.dodge_chance = 0.0
        
        # === NEW: MANA SYSTEM ===
        # Mana stats
        try:
            self.base_max_mana = max(0, int(data.get('mana', 100)))
        except (ValueError, TypeError):
            self.base_max_mana = 100
        self.max_mana = self.base_max_mana
        self.current_mana = data.get('current_mana', self.max_mana)
        try:
            self.base_mana_regen = max(0, int(data.get('mana_regen', 10)))
        except (ValueError, TypeError):
            self.base_mana_regen = 10
        self.mana_regen = self.base_mana_regen
        
        # Magic stats
        try:
            self.base_magic_power = max(0, int(data.get('magic_power', 5)))
        except (ValueError, TypeError):
            self.base_magic_power = 5
        self.magic_power = self.base_magic_power
        try:
            self.base_magic_penetration = max(0.0, float(data.get('magic_penetration', 0.0)))
        except (ValueError, TypeError):
            self.base_magic_penetration = 0.0
        self.magic_penetration = self.base_magic_penetration
        
        # Skills list (skill IDs the player knows)
        self.skills = data.get('skills', [])
        if not isinstance(self.skills, list):
            self.skills = []
        
        # Equipped skills (max 5, displayed on skill bar)
        self.equipped_skills = data.get('equipped_skills', [])
        if not isinstance(self.equipped_skills, list):
            self.equipped_skills = []
        
        # Skill cooldowns (dict of skill_id -> remaining turns)
        self.skill_cooldowns = data.get('skill_cooldowns', {})
        if not isinstance(self.skill_cooldowns, dict):
            self.skill_cooldowns = {}
        
        try:
            self.gold = max(0, int(data.get('gold', 0)))
        except (ValueError, TypeError):
            self.gold = 0
        try:
            self.xp = max(0, int(data.get('xp', 0)))
        except (ValueError, TypeError):
            self.xp = 0
        try:
            self.level = max(1, int(data.get('level', 1)))
        except (ValueError, TypeError):
            self.level = 1
        # Challenge progression (persistent)
        try:
            self.challenge_coins = max(0, int(data.get('challenge_coins', 0)))
        except (ValueError, TypeError):
            self.challenge_coins = 0
        # dict of upgrade_id -> level
        self.permanent_upgrades = data.get('permanent_upgrades', {})
        if not isinstance(self.permanent_upgrades, dict):
            self.permanent_upgrades = {}
        # Points non dépensés à attribuer lors d'un level-up
        try:
            self.unspent_points = max(0, int(data.get('unspent_points', 0)))
        except (ValueError, TypeError):
            self.unspent_points = 0
        # Inventaire simple: dict of item_id -> count
        self.inventory = data.get('inventory', {})
        if not isinstance(self.inventory, dict):
            self.inventory = {}
        # Equipment slots store item ids
        default_equipment = {
            "weapon": None,
            "armor": None,
            "offhand": None,
            "relic1": None,
            "relic2": None,
            "relic3": None
        }
        self.equipment = data.get('equipment', default_equipment)
        if not isinstance(self.equipment, dict):
            self.equipment = default_equipment.copy()
        # Ensure all slots exist (for backward compatibility with old saves)
        for slot in default_equipment:
            if slot not in self.equipment:
                self.equipment[slot] = None
        
        # Game seed for deterministic RNG (shop price increases, mob/shop appearance)
        import random
        import time
        if 'game_seed' in data and data['game_seed'] is not None:
            try:
                self.game_seed = int(data['game_seed'])
            except (ValueError, TypeError):
                self.game_seed = int(time.time() * 1000) % 1000000000
        else:
            # Generate new seed from current time
            self.game_seed = int(time.time() * 1000) % 1000000000
        
        # Shop statistics tracking
        try:
            self.total_items_bought = max(0, int(data.get('total_items_bought', 0)))
        except (ValueError, TypeError):
            self.total_items_bought = 0
        try:
            self.total_gold_spent = max(0, int(data.get('total_gold_spent', 0)))
        except (ValueError, TypeError):
            self.total_gold_spent = 0
        try:
            self.cumulative_price_increase = max(0.0, float(data.get('cumulative_price_increase', 0.0)))
        except (ValueError, TypeError):
            self.cumulative_price_increase = 0.0
        
        # Highest wave reached (for stats)
        try:
            self.highest_wave = max(0, int(data.get('highest_wave', 0)))
        except (ValueError, TypeError):
            self.highest_wave = 0
        
        # Apply agility bonuses on initialization
        self._apply_agility_bonuses()

    @staticmethod
    def _calculate_effective_stat(raw_value, soft_cap, hard_cap):
        """Calculate effective stat with soft and hard caps.
        Below soft_cap: 1:1 ratio
        Between soft_cap and hard_cap: diminishing returns (2:1 ratio)
        Above hard_cap: capped at hard_cap
        """
        if raw_value <= soft_cap:
            return raw_value
        elif raw_value <= hard_cap:
            # Diminishing returns: every 2 points gives 1% after soft cap
            excess = raw_value - soft_cap
            return soft_cap + (excess * 0.5)
        else:
            # Hard capped
            excess = hard_cap - soft_cap
            return soft_cap + (excess * 0.5)
    
    def get_effective_defense_percent(self):
        """Get effective defense as percentage (0-75) with soft cap at 30."""
        return self._calculate_effective_stat(self.defense, 30, 75)
    
    def get_effective_penetration_percent(self):
        """Get effective penetration as percentage (0-75) with soft cap at 50."""
        return self._calculate_effective_stat(self.penetration, 50, 75)

    def take_damage(self, dmg, attacker_penetration=0):
        """Take damage with percentage-based defense reduction.
        
        Args:
            dmg: Raw damage amount
            attacker_penetration: Attacker's penetration stat (reduces defense effectiveness)
        
        Returns:
            Actual damage taken after defense
        """
        # Calculate effective defense percentage (0-75%)
        defense_percent = self.get_effective_defense_percent()
        
        # Calculate effective penetration from attacker (0-75%)
        if attacker_penetration > 0:
            pen_percent = self._calculate_effective_stat(attacker_penetration, 50, 75)
        else:
            pen_percent = 0
        
        # Penetration reduces defense effectiveness
        # Example: 50% pen vs 80% defense = 80% * (1 - 0.50) = 40% effective defense
        effective_defense = defense_percent * (1.0 - (pen_percent / 100.0))
        
        # Apply damage reduction
        damage_multiplier = 1.0 - (effective_defense / 100.0)
        dmg_taken = max(1, int(dmg * damage_multiplier))  # Minimum 1 damage
        
        self.hp = max(0, self.hp - dmg_taken)
        return dmg_taken
    
    def regenerate_mana(self, amount=None):
        """Regenerate mana (called each turn). Returns amount gained."""
        if amount is None:
            amount = self.mana_regen
        old_mana = self.current_mana
        self.current_mana = min(self.max_mana, self.current_mana + amount)
        return self.current_mana - old_mana
    
    def consume_mana(self, cost):
        """Consume mana for skill usage. Returns True if successful."""
        if self.current_mana >= cost:
            self.current_mana -= cost
            return True
        return False
    
    def use_item(self, item_id):
        """Use a consumable item from inventory
        
        Handles:
        - Fixed healing (heal: int)
        - Percentage healing (heal_percent: float 0.0-1.0)
        - Mana restoration (restore_mana: int)
        
        Returns True if item was used successfully
        """
        item = self._load_item_by_id(item_id)
        if not item:
            return False
        
        if item.get('type') != 'consumable':
            return False
        
        if not self.has_item(item_id):
            return False
        
        # Apply effects
        effect = item.get('effect', {})
        
        # Fixed healing
        if 'heal' in effect:
            heal_amount = effect['heal']
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + heal_amount)
            print(f"Healed {self.hp - old_hp} HP")
        
        # Percentage healing
        if 'heal_percent' in effect:
            heal_percent = effect['heal_percent']
            heal_amount = int(self.max_hp * heal_percent)
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + heal_amount)
            print(f"Healed {self.hp - old_hp} HP ({int(heal_percent * 100)}%)")
        
        # Mana restoration
        if 'restore_mana' in effect:
            mana_amount = effect['restore_mana']
            old_mana = self.current_mana
            self.current_mana = min(self.max_mana, self.current_mana + mana_amount)
            print(f"Restored {self.current_mana - old_mana} mana")
        
        # Remove item from inventory
        self.remove_item(item_id, 1)
        return True

    def _apply_agility_bonuses(self):
        """Apply bonuses from agility stat: crit chance and dodge chance with soft/hard caps."""
        if not hasattr(self, 'agility'):
            self.agility = 0
        
        # Crit chance bonus: 0.05% per point (0.0005 as decimal)
        agility_crit_bonus = self.agility * 0.0005
        self.critchance += agility_crit_bonus
        
        # Dodge chance calculation with soft cap at 30% and hard cap at 40%
        # Balanced scaling: starts meaningful but slows down
        if self.agility > 0:
            soft_cap = 0.30  # 30%
            hard_cap = 0.40  # 40%
            
            import math
            # Better early-game scaling while maintaining caps
            # At 10 agility: ~2.3% dodge
            # At 50 agility: ~11% dodge
            # At 150 agility: ~25% dodge
            # At 300 agility: ~30% dodge (soft cap)
            if self.agility <= 300:
                # Exponential growth to soft cap
                self.dodge_chance = soft_cap * (1 - math.exp(-self.agility / 100))
            else:
                # Past soft cap: very slow growth from 30% to 40% hard cap
                excess_agility = self.agility - 300
                # Approaches hard cap asymptotically (needs ~500+ more agility to get close to 40%)
                bonus_dodge = (hard_cap - soft_cap) * (1 - math.exp(-excess_agility / 500))
                self.dodge_chance = soft_cap + bonus_dodge
            
            # Ensure we never exceed hard cap
            self.dodge_chance = min(hard_cap, self.dodge_chance)
        else:
            self.dodge_chance = 0.0

    def gain_xp(self, amount):
        self.xp += amount
        # Supporte plusieurs niveaux d'un coup
        # Exponential scaling: level^1.5 * 100 (more XP needed each level)
        xp_required = int((self.level ** 1.5) * 100)
        while self.xp >= xp_required:
            self.xp -= xp_required
            self.level_up()
            xp_required = int((self.level ** 1.5) * 100)

    def level_up(self):
        self.level += 1
        # Accorde un boost de vie de base et soigne le joueur
        # increase the canonical base max hp so recalculation is deterministic
        self.base_max_hp = getattr(self, 'base_max_hp', self.max_hp) + 10
        self.max_hp = self.base_max_hp
        self.hp = self.max_hp
        # Accord de points de compétence à dépenser manuellement (via l'UI)
        self.unspent_points += 3
        
        # Every 3 levels, grant +1 to all stats automatically
        if self.level % 3 == 0:
            self.base_atk += 1
            self.base_defense += 1
            self.base_max_hp += 5
            self.max_hp = self.base_max_hp
            self.hp = self.max_hp
            self.base_agility = getattr(self, 'base_agility', 0) + 1
            print(f"🎉 Milestone! Level {self.level}: +1 to all stats!")
        
        # Auto-unlock skills that require this level
        self._check_level_unlocks()
        
        # Recalculate derived stats (equipment, permanent upgrades) so level HP stacks with them
        try:
            self._recalc_stats()
        except Exception:
            pass
        print(f"{self.name} est maintenant niveau {self.level} ! (+3 points non dépensés)")

    def spend_point(self, stat: str) -> bool:
        """Dépense un point sur une statistique: 'atk', 'def', 'hp', 'agi'. Retourne True si succès."""
        if self.unspent_points <= 0:
            return False
        if stat == "atk":
            self.base_atk += 1
        elif stat == "def":
            self.base_defense += 1
        elif stat == "hp":
            # increase canonical base max HP without healing the player
            self.base_max_hp = getattr(self, 'base_max_hp', self.max_hp) + 5
        elif stat == "agi" or stat == "agility":
            # increase base agility
            self.base_agility = getattr(self, 'base_agility', 0) + 1
        else:
            return False

        self.unspent_points -= 1
        print(f"{self.name} dépense 1 point sur {stat}. Points restants: {self.unspent_points}")
        
        # For HP stat, preserve current HP to avoid healing
        if stat == "hp":
            current_hp = self.hp
            self._recalc_stats()
            # Restore the exact HP value (no healing)
            self.hp = min(current_hp, self.max_hp)
        else:
            # For other stats, recalc normally
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
        # Map item types to equipment slots
        slot_mapping = {
            "weapon": "weapon",
            "armor": "armor",
            "offhand": "offhand",
            "relic": None  # Will auto-find first empty relic slot
        }
        
        slot = slot_mapping.get(itype)
        if slot is None and itype == "relic":
            # Find first empty relic slot
            for relic_slot in ["relic1", "relic2", "relic3"]:
                if not self.equipment.get(relic_slot):
                    slot = relic_slot
                    break
            if not slot:
                # All relic slots full, add to inventory
                self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
                return
        
        if slot and (itype in ["weapon", "armor", "offhand", "relic"]):
            prev_id = self.equipment.get(slot)
            # If same item already equipped, treat as spare and add to inventory
            if prev_id == item_id:
                self.inventory[item_id] = self.inventory.get(item_id, 0) + 1
                return
            # Equip the new item and return previous to inventory (if any)
            if prev_id:
                self.inventory[prev_id] = self.inventory.get(prev_id, 0) + 1
            self.equipment[slot] = item_id
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
        
        # Map item types to slots
        slot_mapping = {
            'weapon': 'weapon',
            'armor': 'armor',
            'offhand': 'offhand'
        }
        
        slot = slot_mapping.get(itype)
        
        # Special handling for relics - find first empty slot
        if itype == 'relic':
            for relic_slot in ['relic1', 'relic2', 'relic3']:
                if not self.equipment.get(relic_slot):
                    slot = relic_slot
                    break
            if not slot:
                return False  # All relic slots full
        
        if slot:
            prev_id = self.equipment.get(slot)
            if prev_id == item_id:
                return False
            # return previous item to inventory
            if prev_id:
                self.inventory[prev_id] = self.inventory.get(prev_id, 0) + 1
            self.equipment[slot] = item_id
            # Check for skill unlocks from this item
            self._check_item_unlocks(item_id)
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
        # remember previous max and hp so we can preserve the hp fraction when max changes
        prev_max = getattr(self, 'max_hp', None)
        prev_hp = getattr(self, 'hp', None)

        # start from base (reset derived stats)
        self.atk = getattr(self, 'base_atk', 0)
        self.defense = getattr(self, 'base_defense', 0)
        # reset max_hp to canonical base before applying equipment/upgrades
        # but guard against a corrupted or implausibly large base_max_hp by
        # clamping it relative to the previous max to avoid large jumps.
        bmh = getattr(self, 'base_max_hp', None)
        if bmh is None:
            self.max_hp = getattr(self, 'max_hp', 0)
        else:
            try:
                if prev_max and prev_max > 0 and bmh > prev_max * 4:
                    # base_max_hp is suspiciously large; clamp to previous max
                    self.base_max_hp = int(prev_max)
                    self.max_hp = int(prev_max)
                elif bmh > 10000:
                    # absolute safety cap
                    cap = max(1000, prev_max or 1000)
                    self.base_max_hp = int(cap)
                    self.max_hp = int(cap)
                else:
                    self.max_hp = int(bmh)
            except Exception:
                self.max_hp = int(getattr(self, 'max_hp', 0))
        # reset crit stats to base
        self.critchance = getattr(self, 'base_critchance', 0.0)
        self.critdamage = getattr(self, 'base_critdamage', 1.5)
        # reset penetration to base
        self.penetration = getattr(self, 'base_penetration', 0.0)
        # reset agility to base
        self.agility = getattr(self, 'base_agility', 0)
        # reset mana stats to base
        self.max_mana = getattr(self, 'base_max_mana', 100)
        self.mana_regen = getattr(self, 'base_mana_regen', 10)
        # reset magic stats to base
        self.magic_power = getattr(self, 'base_magic_power', 5)
        self.magic_penetration = getattr(self, 'base_magic_penetration', 0.0)
        # Apply bonuses from all equipment slots
        for slot_name, item_id in self.equipment.items():
            if not item_id:
                continue
            equipped_item = self._load_item_by_id(item_id)
            if not equipped_item:
                continue
            
            # Add all possible stat bonuses
            if equipped_item.get('attack'):
                self.atk += equipped_item.get('attack', 0)
            if equipped_item.get('defense'):
                self.defense += equipped_item.get('defense', 0)
            if equipped_item.get('critchance'):
                try:
                    self.critchance += float(equipped_item.get('critchance', 0.0))
                except Exception:
                    pass
            if equipped_item.get('critdamage'):
                try:
                    self.critdamage += float(equipped_item.get('critdamage', 0.0))
                except Exception:
                    pass
            if equipped_item.get('penetration'):
                try:
                    self.penetration += float(equipped_item.get('penetration', 0.0))
                except Exception:
                    pass
            # Relics and offhand can provide HP bonuses
            if equipped_item.get('max_hp'):
                try:
                    self.max_hp += int(equipped_item.get('max_hp', 0))
                except Exception:
                    pass
            # Magic stats from equipment
            if equipped_item.get('magic_power'):
                try:
                    self.magic_power += int(equipped_item.get('magic_power', 0))
                except Exception:
                    pass
            if equipped_item.get('magic_penetration'):
                try:
                    self.magic_penetration += float(equipped_item.get('magic_penetration', 0.0))
                except Exception:
                    pass
            if equipped_item.get('max_mana'):
                try:
                    self.max_mana += int(equipped_item.get('max_mana', 0))
                except Exception:
                    pass
            if equipped_item.get('mana_regen'):
                try:
                    self.mana_regen += int(equipped_item.get('mana_regen', 0))
                except Exception:
                    pass

        # Apply permanent upgrades (data-driven) to derived stats only.
        # This avoids mutating the canonical base_* attributes repeatedly when _recalc_stats is called.
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
                                # map base_* stat names to derived fields
                                s = stat
                                # canonical mapping: base_atk -> atk, base_defense -> defense, base_critchance -> critchance, base_critdamage -> critdamage
                                if s.startswith('base_'):
                                    s = s[len('base_'):]
                                # Apply to the appropriate derived stat
                                if s in ('atk', 'attack'):
                                    self.atk += val * int(lvl)
                                elif s in ('def', 'defense', 'base_def'):
                                    self.defense += val * int(lvl)
                                elif s in ('max_hp', 'hp'):
                                    # increase max_hp by computed delta on top of base
                                    try:
                                        delta = int(val) * int(lvl)
                                    except Exception:
                                        try:
                                            delta = int(float(val) * int(lvl))
                                        except Exception:
                                            delta = 0
                                    self.max_hp = getattr(self, 'max_hp', 0) + delta
                                elif s in ('critchance',):
                                    self.critchance += float(val) * int(lvl)
                                elif s in ('critdamage', 'crit_mult'):
                                    self.critdamage += float(val) * int(lvl)
                                elif s in ('penetration', 'pen'):
                                    self.penetration += float(val) * int(lvl)
                                elif s in ('agility', 'agi'):
                                    self.agility += int(val) * int(lvl)
                                else:
                                    # fallback: apply to attribute if exists (but don't mutate base_* names)
                                    try:
                                        cur = getattr(self, s, 0)
                                        setattr(self, s, cur + val * int(lvl))
                                    except Exception:
                                        pass
                        except Exception:
                            pass
        except Exception:
            pass

        # Apply agility-based bonuses
        self._apply_agility_bonuses()

        # If max_hp changed, preserve the player's current HP proportionally.
        try:
            if prev_max and prev_hp is not None:
                # if player was at full HP before, keep them full
                if prev_max > 0 and prev_hp >= prev_max:
                    self.hp = getattr(self, 'max_hp', prev_hp)
                elif prev_max > 0:
                    frac = float(prev_hp) / float(prev_max)
                    # apply fraction to new max and clamp
                    new_hp = int(frac * float(getattr(self, 'max_hp', prev_max)))
                    self.hp = min(getattr(self, 'max_hp', new_hp), new_hp)
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
    
    def unlock_skill(self, skill_id):
        """Unlock a new skill. Returns True if newly unlocked, False if already known."""
        if not hasattr(self, 'skills'):
            self.skills = []
        if skill_id not in self.skills:
            self.skills.append(skill_id)
            print(f"✨ New skill unlocked: {skill_id}")
            return True
        return False
    
    def _check_level_unlocks(self):
        """Check all skills and unlock any that require current level or lower"""
        import json
        import os
        try:
            skills_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'skills.json')
            with open(skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both dict and array formats
            if isinstance(data, dict) and 'skills' in data:
                all_skills = data['skills']
            elif isinstance(data, list):
                all_skills = data
            else:
                all_skills = data  # Assume it's already in the right format
            
            for skill_data in all_skills:
                skill_id = skill_data.get('id')
                unlock_req = skill_data.get('unlock_requirements', {})
                required_level = unlock_req.get('level')
                if required_level and self.level >= required_level and skill_id:
                    self.unlock_skill(skill_id)
        except Exception as e:
            print(f"Warning: Failed to check level unlocks: {e}")
    
    def _check_item_unlocks(self, item_id):
        """Check all skills and unlock any that require this specific item to be equipped"""
        import json
        import os
        try:
            skills_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'skills.json')
            with open(skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both dict and array formats
            if isinstance(data, dict) and 'skills' in data:
                all_skills = data['skills']
            elif isinstance(data, list):
                all_skills = data
            else:
                all_skills = data  # Assume it's already in the right format
            
            for skill_data in all_skills:
                skill_id = skill_data.get('id')
                unlock_req = skill_data.get('unlock_requirements', {})
                required_item = unlock_req.get('item_equipped')
                if required_item == item_id and skill_id:
                    self.unlock_skill(skill_id)
        except Exception as e:
            print(f"Warning: Failed to check item unlocks: {e}")
    
    def open_container(self, container_item):
        """Open a container item and grant loot from its loot pool
        
        Returns list of granted items
        """
        loot_pool = container_item.get('loot_pool', [])
        granted_items = []
        
        import random
        for loot_entry in loot_pool:
            chance = loot_entry.get('chance', 0.0)
            if random.random() < chance:
                item_id = loot_entry.get('item_id')
                skill_id = loot_entry.get('skill_id')
                qty = loot_entry.get('qty', 1)
                
                if item_id:
                    # Grant item
                    item_def = self._load_item_by_id(item_id)
                    if item_def:
                        for _ in range(qty):
                            self.add_item(item_def, auto_equip=False)
                        granted_items.append(('item', item_id, qty))
                        print(f"📦 Container grants: {item_def.get('name', item_id)} x{qty}")
                
                if skill_id:
                    # Grant skill
                    if self.unlock_skill(skill_id):
                        granted_items.append(('skill', skill_id, 1))
        
        return granted_items
