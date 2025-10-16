import pygame
from pathlib import Path
import sys
sys.path.insert(0, str(Path('MainGame/src').resolve()))
from ui_manager import UIManager

pygame.init()
scr = pygame.display.set_mode((800,600))
ui = UIManager(scr, assets_path=Path('MainGame/assets'), data_path=Path('MainGame/data'))
class Dummy:
    def __init__(self):
        self.hp=100
        self.max_hp=100
        self.gold=50
        self.level=2
        self.xp=30
        self.equipment={'weapon':None,'armor':None}
        self.unspent_points=1
        self.name='Test'
player = Dummy()
# call draw once
ui.draw(player, None)
pygame.image.save(scr, 'tmp_ui_test.png')
pygame.quit()
print('wrote tmp_ui_test.png')
