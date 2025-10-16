# src/battle_system.py
import time
try:
    from enemy import Enemy
except Exception:
    from .enemy import Enemy

class BattleSystem:
    def __init__(self, player):
        self.player = player
        self.wave = 1
        self.enemy = Enemy.random_enemy(self.wave)
        self.turn = "player"
        self.last_action_time = 0
        self.action_delay = 0.5  # petit délai visuel
        # Whether the next wave is a shop instead of a fight
        self.in_shop = False

    def player_attack(self):
        """Action du joueur via un bouton."""
        if self.turn != "player":
            return  # ignore si ce n’est pas ton tour

        dmg = self.player.atk
        self.enemy.take_damage(dmg)
        print(f"{self.player.name} inflige {dmg} à {self.enemy.name} !")

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
            if time.time() - self.last_action_time >= self.action_delay:
                dmg = self.enemy.atk
                self.player.take_damage(dmg)
                print(f"{self.enemy.name} inflige {dmg} à {self.player.name} !")

                if self.player.is_dead():
                    print(f"{self.player.name} est vaincu... 💀")
                    # Do not auto-respawn here; main loop will handle game over

                self.turn = "player"

    def next_wave(self):
        self.wave += 1
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
