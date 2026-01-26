# src/battle_system.py
import time
try:
    from enemy import Enemy
except Exception:
    from .enemy import Enemy
import random

class BattleSystem:
    def __init__(self, player):
        self.player = player
        self.wave = 1
        self.enemy = Enemy.random_enemy(self.wave)
        self.turn = "player"
        self.last_action_time = 0
        self.action_delay = 0.9  # petit délai visuel — make turns less instant
        # Whether the next wave is a shop instead of a fight
        self.in_shop = False
        # Queue of recent damage events for UI (list of dicts: target, amount, time, is_crit)
        self.damage_events = []

    def player_attack(self):
        """Action du joueur via un bouton."""
        if self.turn != "player":
            return  # ignore si ce n’est pas ton tour        
        # Safety check: ensure enemy exists
        if not self.enemy or self.enemy.is_dead():
            print("No enemy to attack!")
            return
        # base damage
        base_dmg = getattr(self.player, 'atk', 0)
        # roll for critical hit using player's crit chance (0.0 - 1.0)
        try:
            is_crit = random.random() < float(getattr(self.player, 'critchance', 0.0))
        except Exception:
            is_crit = False

        if is_crit:
            crit_mult = float(getattr(self.player, 'critdamage', 1.5))
            dmg = int(round(base_dmg * crit_mult))
        else:
            dmg = int(base_dmg)

        # apply damage to enemy (pass player penetration)
        player_pen = getattr(self.player, 'penetration', 0)
        dmg_dealt = self.enemy.take_damage(dmg, player_pen)
        # register damage event for UI
        try:
            self.damage_events.append({
                'target': 'enemy',
                'amount': int(dmg_dealt),
                'time': time.time(),
                'is_crit': bool(is_crit),
            })
        except Exception:
            pass
        if is_crit:
            print(f"CRIT! {self.player.name} inflige {dmg_dealt} (x{crit_mult}) à {self.enemy.name} !")
        else:
            print(f"{self.player.name} inflige {dmg_dealt} à {self.enemy.name} !")

        if self.enemy.is_dead():
            print(f"{self.enemy.name} est vaincu !")
            self.player.gold += self.enemy.gold
            self.player.gain_xp(self.enemy.xp)
            # handle potential drops before moving to next wave
            self._process_drops(self.enemy)
            self.next_wave()
        else:
            self.turn = "enemy"
            self.last_action_time = time.time()

    def update(self):
        """Tour automatique de l’ennemi après ton attaque."""
        if self.turn == "enemy":
            # Safety check: ensure enemy exists before attacking
            if not self.enemy or self.enemy.is_dead():
                self.turn = "player"
                return
            
            if time.time() - self.last_action_time >= self.action_delay:
                # Check if player dodges the attack
                player_dodge = getattr(self.player, 'dodge_chance', 0.0)
                dodged = random.random() < player_dodge
                
                if dodged:
                    # Player dodged the attack!
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': 0,
                            'time': time.time(),
                            'is_crit': False,
                            'dodged': True,
                        })
                    except Exception:
                        pass
                    print(f"{self.player.name} esquive l'attaque de {self.enemy.name}!")
                else:
                    dmg = self.enemy.atk
                    # Enemies don't have penetration (for now), pass 0
                    enemy_pen = getattr(self.enemy, 'penetration', 0)
                    # apply damage and capture the actual damage taken after defense
                    dmg_taken = self.player.take_damage(dmg, enemy_pen)
                    # register damage event for UI with post-defense damage
                    try:
                        self.damage_events.append({
                            'target': 'player',
                            'amount': int(dmg_taken),
                            'time': time.time(),
                            'is_crit': False,
                        })
                    except Exception:
                        pass
                    print(f"{self.enemy.name} inflige {dmg_taken} à {self.player.name} !")

                    if self.player.is_dead():
                        print(f"{self.player.name} est vaincu... 💀")
                    # Do not auto-respawn here; main loop will handle game over

                self.turn = "player"

    def next_wave(self):
        self.wave += 1
        # Award challenge coins: +1 every 10 waves, +1 extra every 20 waves
        try:
            reward = 0
            if self.wave % 10 == 0:
                reward += 1
            if self.wave % 20 == 0:
                reward += 1
            if reward > 0 and hasattr(self.player, 'challenge_coins'):
                self.player.challenge_coins = getattr(self.player, 'challenge_coins', 0) + reward
                # Add a short notification event to be displayed by UI
                try:
                    self.damage_events.append({'type': 'coin_reward', 'amount': reward, 'time': time.time()})
                except Exception:
                    pass
        except Exception:
            pass
        
        # Apply wave-based price increase (1-15% per wave, seeded)
        try:
            if hasattr(self.player, 'game_seed') and self.player.game_seed is not None:
                # Use player seed + wave to determine this wave's price increase
                import random
                wave_seed = (self.player.game_seed + self.wave * 9973) % 1000000007
                rng = random.Random(wave_seed)
                # Random increase between 0.01 (1%) and 0.15 (15%)
                wave_increase = rng.uniform(0.01, 0.15)
                # Add to cumulative price increase
                if hasattr(self.player, 'cumulative_price_increase'):
                    self.player.cumulative_price_increase = getattr(self.player, 'cumulative_price_increase', 0.0) + wave_increase
        except Exception as e:
            print(f"Error calculating price increase: {e}")
        
        # Update highest wave
        if hasattr(self.player, 'highest_wave'):
            self.player.highest_wave = max(getattr(self.player, 'highest_wave', 0), self.wave)
        
        # Decide whether next wave is a shop — guaranteed every 10th wave, otherwise 10% chance
        import random
        if self.wave % 10 == 0:
            self.in_shop = True
        else:
            self.in_shop = random.random() < 0.10
        if not self.in_shop:
            self.enemy = Enemy.random_enemy(self.wave)
            print(f"👹 Nouvelle vague : {self.enemy.name}")
            self.turn = "player"
        else:
            self.enemy = None
            print(f"🛒 Shop opens at wave {self.wave}")
    
    def _process_drops(self, enemy):
        """Check items.json for droppable items matching the enemy category and roll.
        Adds items to player.inventory via player.add_item on success.
        """
        try:
            from pathlib import Path
            import json
            import random

            base = Path(__file__).resolve().parents[1]
            items_path = base / 'data' / 'items.json'
            if not items_path.exists():
                items = []
            else:
                with open(items_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = data.get('items', [])

            # global droppable items table
            for it in items:
                if not it.get('droppable'):
                    continue
                dropped_by = it.get('dropped_by')
                # if dropped_by not set, skip
                if not dropped_by:
                    continue
                # allow lists or single string
                if isinstance(dropped_by, list):
                    ok = enemy.category in dropped_by
                else:
                    ok = (enemy.category == dropped_by)
                if not ok:
                    continue
                # compute chance
                chance = float(it.get('drop_chance', 0.25))
                if random.random() < chance:
                    # grant the item
                    print(f"Loot trouvé: {it.get('name')} de {enemy.name}")
                    # call add_item so equipment auto-equip behavior is respected
                    self.player.add_item(it)

            # Also check per-monster drops in monsters.json if present (supports qty ranges)
            monsters_path = base / 'data' / 'monsters.json'
            if monsters_path.exists():
                with open(monsters_path, 'r', encoding='utf-8') as f:
                    mdata = json.load(f)
                for mon in mdata.get('enemies', []):
                    if mon.get('id') == getattr(enemy, 'id', None):
                        for drop in mon.get('drops', []):
                            chance = float(drop.get('chance', 0.0))
                            if random.random() < chance:
                                iid = drop.get('item_id')
                                qmin = int(drop.get('qty_min', 1))
                                qmax = int(drop.get('qty_max', qmin))
                                qty = random.randint(qmin, qmax)
                                # find item def in items.json
                                item_def = None
                                for it in items:
                                    if it.get('id') == iid:
                                        item_def = it
                                        break
                                if not item_def:
                                    item_def = {'id': iid, 'name': iid, 'type': 'misc'}
                                print(f"Loot (monster table): {item_def.get('name')} x{qty} from {enemy.name}")
                                for _ in range(qty):
                                    self.player.add_item(item_def)
                        break
        except Exception as e:
            print("Erreur lors du traitement des drops:", e)
