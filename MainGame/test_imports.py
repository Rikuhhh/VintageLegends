import importlib
import sys
mods = ['src.player','src.enemy','src.battle_system','src.ui_manager']
errs = []
for m in mods:
    try:
        importlib.invalidate_caches()
        importlib.import_module(m)
        print('OK', m)
    except Exception as e:
        print('ERR', m, e)
        errs.append((m,str(e)))
if errs:
    sys.exit(1)
print('All imports OK')
