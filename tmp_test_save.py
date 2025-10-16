from MainGame.src.save_manager import SaveManager
from pathlib import Path
class B:
    def __init__(self):
        self.wave=5
        class E:
            def __init__(self):
                self.hp=7
                self.id='wolf'
        self.enemy=E()

class P:
    def __init__(self):
        self.name='T'
        self.hp=10
        self.max_hp=10
        self.atk=5
        self.defense=2
        self.gold=12
        self.xp=0
        self.level=1
        self.inventory={}
        self.equipment={'weapon':None,'armor':None}
        self.highest_wave=3

s=SaveManager(Path('MainGame/saves'))
try:
    s.save(P(), battle=B())
    print('Saved OK')
except Exception as e:
    print('Save failed', e)
