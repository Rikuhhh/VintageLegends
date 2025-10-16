# src/enemy.py
import random
import json
from pathlib import Path


class Enemy:
    def __init__(self, name="Slime", hp=30, atk=5, gold=10, xp=15, id=None):
        self.id = id
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.gold = gold
        self.xp = xp
        self.category = None

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
    def _scale_value(base_val, wave, per_wave_pct):
        try:
            factor = 1.0 + per_wave_pct * wave
            return max(1, int(round(base_val * factor)))
        except Exception:
            return int(base_val)

    @staticmethod
    def random_enemy(wave=1):
        """Create an enemy definition based on monsters.json rules and scaling.
        Rules:
        - Bosses prioritized on multiples of 10
        - Minibosses on multiples of 5
        - Elites are rarer than normal
        - min_wave/max_wave (0 means ignore)
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

        hp = Enemy._scale_value(hp_base, wave, hp_pct)
        atk = Enemy._scale_value(atk_base, wave, atk_pct)
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
        # classification comes from monster def (normal/elite/miniboss/boss). Category is an optional tag like 'demon'/'dragon'.
        e.classification = chosen.get('classification')
        e.category = chosen.get('category', chosen.get('classification'))
        return e

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def is_dead(self):
        return self.hp <= 0
