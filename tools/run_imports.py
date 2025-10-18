import sys
sys.path.insert(0, r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends')
import importlib
modules = ['MainGame.src.modals','MainGame.src.main','MainGame.src.shop']
for m in modules:
    try:
        importlib.import_module(m)
        print('OK', m)
    except Exception as e:
        print('FAIL', m, e)
        raise
print('ALL IMPORTS OK')
