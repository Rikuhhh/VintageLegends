import importlib, sys
from pathlib import Path
# ensure src packages import correctly
sys.path.insert(0, str(Path('MainGame/src').resolve()))
m = importlib.import_module('main')
bg = getattr(m, 'background', None)
ps = getattr(m, 'player_sprite', None)
print('background size:', bg.get_size() if bg else None, 'player_sprite loaded:', ps is not None)
