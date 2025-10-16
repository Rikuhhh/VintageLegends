# src/battle_system.py
import time
from enemy import Enemy

class BattleSystem:
    def __init__(self, player):
        self.player = player
        self.wave = 1
        self.enemy = Enemy.random_enemy(self.wave)
        self.turn = "player"
        self.last_action_time = 0
        self.action_delay = 0.5  # petit délai visuel

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
                    self.player.hp = self.player.max_hp // 2  # respawn partiel

                self.turn = "player"

    def next_wave(self):
        self.wave += 1
        self.enemy = Enemy.random_enemy(self.wave)
        print(f"👹 Nouvelle vague : {self.enemy.name}")
        self.turn = "player"
