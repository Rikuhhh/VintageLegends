# src/player.py
class Player:
    def __init__(self, data):
        self.name = data.get("name", "Inconnu")
        self.max_hp = data.get("hp", 100)
        self.hp = self.max_hp
        self.atk = data.get("atk", 10)
        self.defense = data.get("def", 5)
        self.gold = 0
        self.xp = 0
        self.level = 1

    def take_damage(self, dmg):
        dmg_taken = max(1, dmg - self.defense)
        self.hp = max(0, self.hp - dmg_taken)
        return dmg_taken

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.level * 100:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.max_hp += 10
        self.atk += 2
        self.defense += 1
        self.hp = self.max_hp
        print(f"{self.name} est maintenant niveau {self.level} !")

    def is_dead(self):
        return self.hp <= 0
