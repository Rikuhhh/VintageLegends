# src/enemy.py
import random

class Enemy:
    def __init__(self, name="Slime", hp=30, atk=5, gold=10, xp=15):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.gold = gold
        self.xp = xp

    @staticmethod
    def random_enemy(wave=1):
        """Crée un ennemi basique basé sur la vague actuelle."""
        hp = 20 + wave * 5
        atk = 5 + wave * 2
        gold = 10 + wave * 3
        xp = 10 + wave * 4
        return Enemy(name=f"Slime Lv.{wave}", hp=hp, atk=atk, gold=gold, xp=xp)

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def is_dead(self):
        return self.hp <= 0
