from MainGame.src.save_manager import SaveManager
from pathlib import Path
class P:
    def __init__(self):
        self.name='T'
        self.hp=55
        self.max_hp=180
        self.base_atk=12
        self.base_defense=6
        self.atk=12
        self.defense=6
        self.gold=0
        self.xp=0
        self.level=1
        self.inventory={}
        self.equipment={'weapon':None,'armor':None}
        self.highest_wave=0

s=SaveManager(Path('MainGame/saves'))
s.save(P())
import json
with open('MainGame/saves/save.json','r',encoding='utf-8') as f:
    d=json.load(f)
print('saved max_hp:', d.get('max_hp'), 'base_atk:', d.get('base_atk'))
