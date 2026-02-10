# src/enemy.py
import random
import json
from pathlib import Path


class Enemy:
    def __init__(self, name="Slime", hp=30, atk=5, gold=10, xp=15, id=None):
        self.id = id
        self.name = str(name)
        try:
            self.hp = max(1, int(hp))
            self.max_hp = self.hp
        except (ValueError, TypeError):
            self.hp = 30
            self.max_hp = 30
        try:
            self.atk = max(1, int(atk))
        except (ValueError, TypeError):
            self.atk = 5
        try:
            self.gold = max(0, int(gold))
        except (ValueError, TypeError):
            self.gold = 10
        try:
            self.xp = max(0, int(xp))
        except (ValueError, TypeError):
            self.xp = 15
        self.category = None
        self.classification = None
        # Defense stored as raw value, will be converted to % when calculating damage
        # Initialized to 0, will be set later when creating from monster data
        self.defense = 0
        # Magic defense (separate from physical defense)
        self.magic_defense = 0
        # Penetration stat (most enemies won't have this)
        self.penetration = 0.0

    @staticmethod
    def _load_monsters():
        try:
            base = Path(__file__).resolve().parents[1]
            path = base / 'data' / 'monsters.json'
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            return None
        return None

    @staticmethod
    def _in_wave_range(mon_def, wave):
        # min_wave / max_wave behavior: if 0 or missing, ignore
        minw = int(mon_def.get('min_wave', 0) or 0)
        maxw = int(mon_def.get('max_wave', 0) or 0)
        if minw > 0 and wave < minw:
            return False
        if maxw > 0 and wave > maxw:
            return False
        # spawn_on_wave_multiple_of override
        mult = mon_def.get('spawn_on_wave_multiple_of')
        if mult:
            try:
                mult = int(mult)
                if mult > 0 and (wave % mult) != 0:
                    return False
            except Exception:
                pass
        return True

    @staticmethod
    def _scale_value(base_val, wave, per_wave_pct, flat_per_5waves=0, is_boss=False):
        try:
            # Reduce percentage scaling for normal mobs (not bosses)
            if not is_boss:
                per_wave_pct = per_wave_pct * 0.6  # 40% reduction in % scaling
            
            # Add flat scaling every 5 waves
            flat_bonus = (wave // 5) * flat_per_5waves
            
            factor = 1.0 + per_wave_pct * wave
            return max(1, int(round(base_val * factor + flat_bonus)))
        except Exception:
            return int(base_val)

    @staticmethod
    def random_enemy(wave=1, allowed_categories=None):
        """Create an enemy definition based on monsters.json rules and scaling.
        Rules:
        - Bosses prioritized on multiples of 10
        - Minibosses on multiples of 5
        - Elites are rarer than normal
        - min_wave/max_wave (0 means ignore)
        - allowed_categories: list of category strings to filter by (from zones)
        """
        data = Enemy._load_monsters()
        if not data:
            # fallback to previous simple scaling
            hp = 20 + wave * 5
            atk = 5 + wave * 2
            gold = 10 + wave * 3
            xp = 10 + wave * 4
            return Enemy(name=f"Slime Lv.{wave}", hp=hp, atk=atk, gold=gold, xp=xp)

        enemies = data.get('enemies', [])
        scaling = data.get('scaling_notes', {})
        hp_pct = float(scaling.get('hp_scale_per_wave_pct', 0.06))
        atk_pct = float(scaling.get('atk_scale_per_wave_pct', 0.025))
        # selection pools
        bosses = []
        minibosses = []
        elites = []
        normals = []
        for mon in enemies:
            if not Enemy._in_wave_range(mon, wave):
                continue
            # Filter by allowed categories if specified
            if allowed_categories is not None:
                mon_category = mon.get('category')
                if mon_category not in allowed_categories:
                    continue
            cls = mon.get('classification', 'normal')
            if cls == 'boss':
                bosses.append(mon)
            elif cls == 'miniboss':
                minibosses.append(mon)
            elif cls == 'elite':
                elites.append(mon)
            else:
                normals.append(mon)

        chosen = None
        # Boss on multiples of 10
        if wave % 10 == 0 and bosses:
            chosen = random.choice(bosses)
        # Miniboss on multiples of 5
        elif wave % 5 == 0 and minibosses:
            chosen = random.choice(minibosses)
        else:
            # regular selection: combine normals and elites with weights
            pool = []
            weights = []
            for n in normals:
                pool.append(n)
                weights.append(1.0)
            for e in elites:
                pool.append(e)
                # make elites rarer; reduce weight
                weights.append(0.15)
            if pool:
                # normalize weights and choose
                total = sum(weights)
                r = random.random() * total
                upto = 0
                for p, w in zip(pool, weights):
                    if upto + w >= r:
                        chosen = p
                        break
                    upto += w

        if not chosen:
            # fallback to a normal or slime
            if normals:
                chosen = random.choice(normals)
            else:
                hp = 20 + wave * 5
                atk = 5 + wave * 2
                gold = 10 + wave * 3
                xp = 10 + wave * 4
                return Enemy(name=f"Slime Lv.{wave}", hp=hp, atk=atk, gold=gold, xp=xp)

        # Build stats from chosen def
        hp_base = int(chosen.get('hp_base', 10))
        atk_base = int(chosen.get('atk_base', 1))
        gold_base = int(chosen.get('gold_base', 1))
        xp_base = int(chosen.get('xp_base', 1))
        def_base = int(chosen.get('def_base', 0))
        magic_def_base = int(chosen.get('magic_def_base', 0))
        pen_base = float(chosen.get('pen_base', 0.0))

        hp = Enemy._scale_value(hp_base, wave, hp_pct, flat_per_5waves=10, is_boss=(chosen.get('classification') in ('boss', 'miniboss')))
        atk = Enemy._scale_value(atk_base, wave, atk_pct, flat_per_5waves=1, is_boss=(chosen.get('classification') in ('boss', 'miniboss')))
        # Defense scales slower (0.015 per wave instead of 0.025)
        defense = Enemy._scale_value(def_base, wave, 0.015, flat_per_5waves=1, is_boss=(chosen.get('classification') in ('boss', 'miniboss')))
        # Magic defense scales same as physical defense
        magic_defense = Enemy._scale_value(magic_def_base, wave, 0.015, flat_per_5waves=1, is_boss=(chosen.get('classification') in ('boss', 'miniboss')))
        # gold/xp scaling: use simple formulas if provided in scaling_notes
        try:
            gold = int(round(gold_base * (1 + wave * 0.05)))
        except Exception:
            gold = gold_base
        try:
            xp = int(round(xp_base * (1 + wave * 0.06)))
        except Exception:
            xp = xp_base

        e = Enemy(name=f"{chosen.get('name', 'Enemy')} Lv.{wave}", hp=hp, atk=atk, gold=gold, xp=xp, id=chosen.get('id'))
        # Add defense and penetration
        e.defense = defense
        e.magic_defense = magic_defense
        e.penetration = pen_base  # Penetration doesn't scale with wave for enemies
        # classification comes from monster def (normal/elite/miniboss/boss). Category is an optional tag like 'demon'/'dragon'.
        e.classification = chosen.get('classification', 'normal')
        # Ensure category is set - fall back to classification if not specified
        e.category = chosen.get('category', chosen.get('classification', 'normal'))
        # Add image attribute
        e.image = chosen.get('image', None)
        return e

    @staticmethod
    def from_id(enemy_id, wave=1):
        """Create an enemy by id using the same scaling rules as random_enemy."""
        data = Enemy._load_monsters()
        if not data:
            return None

        enemies = data.get('enemies', [])
        chosen = None
        for mon in enemies:
            if mon.get('id') == enemy_id:
                chosen = mon
                break

        if not chosen:
            return None

        scaling = data.get('scaling_notes', {})
        hp_pct = float(scaling.get('hp_scale_per_wave_pct', 0.06))
        atk_pct = float(scaling.get('atk_scale_per_wave_pct', 0.025))

        hp_base = int(chosen.get('hp_base', 10))
        atk_base = int(chosen.get('atk_base', 1))
        gold_base = int(chosen.get('gold_base', 1))
        xp_base = int(chosen.get('xp_base', 1))
        def_base = int(chosen.get('def_base', 0))
        magic_def_base = int(chosen.get('magic_def_base', 0))
        pen_base = float(chosen.get('pen_base', 0.0))

        is_boss = chosen.get('classification') in ('boss', 'miniboss')
        hp = Enemy._scale_value(hp_base, wave, hp_pct, flat_per_5waves=10, is_boss=is_boss)
        atk = Enemy._scale_value(atk_base, wave, atk_pct, flat_per_5waves=1, is_boss=is_boss)
        defense = Enemy._scale_value(def_base, wave, 0.015, flat_per_5waves=1, is_boss=is_boss)
        magic_defense = Enemy._scale_value(magic_def_base, wave, 0.015, flat_per_5waves=1, is_boss=is_boss)
        try:
            gold = int(round(gold_base * (1 + wave * 0.05)))
        except Exception:
            gold = gold_base
        try:
            xp = int(round(xp_base * (1 + wave * 0.06)))
        except Exception:
            xp = xp_base

        e = Enemy(name=f"{chosen.get('name', 'Enemy')} Lv.{wave}", hp=hp, atk=atk, gold=gold, xp=xp, id=chosen.get('id'))
        e.defense = defense
        e.magic_defense = magic_defense
        e.penetration = pen_base
        e.classification = chosen.get('classification', 'normal')
        e.category = chosen.get('category', chosen.get('classification', 'normal'))
        e.image = chosen.get('image', None)
        return e
    
    @property
    def is_boss(self):
        """Returns True if this enemy is a boss or miniboss"""
        return self.classification in ('boss', 'miniboss')

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

    def take_damage(self, dmg, attacker_penetration=0, effect_manager=None):
        """Take damage with percentage-based defense reduction.
        
        Args:
            dmg: Raw damage amount
            attacker_penetration: Attacker's penetration stat (reduces defense effectiveness)
            effect_manager: EffectManager to apply active buff/debuff modifiers
        
        Returns:
            Actual damage taken after defense
        """
        # Apply active effect modifiers to defense
        defense_modifiers = 0
        if effect_manager:
            stat_modifiers = effect_manager.apply_active_effects(self)
            defense_modifiers = stat_modifiers.get('def', 0)
        
        # Calculate effective defense percentage (0-75%) with buffs/debuffs
        effective_defense_stat = self.defense + defense_modifiers
        defense_percent = self._calculate_effective_stat(effective_defense_stat, 30, 75)
        
        # Calculate effective penetration from attacker (0-75%)
        if attacker_penetration > 0:
            pen_percent = self._calculate_effective_stat(attacker_penetration, 50, 75)
        else:
            pen_percent = 0
        
        # Penetration reduces defense effectiveness
        effective_defense = defense_percent * (1.0 - (pen_percent / 100.0))
        
        # Apply damage reduction
        damage_multiplier = 1.0 - (effective_defense / 100.0)
        dmg_taken = max(1, int(dmg * damage_multiplier))  # Minimum 1 damage
        
        self.hp = max(0, self.hp - dmg_taken)
        return dmg_taken

    def is_dead(self):
        return self.hp <= 0
