import sys
sys.path.insert(0, r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends')
import importlib
try:
    importlib.import_module('MainGame.src.modals')
    importlib.import_module('MainGame.src.main')
    importlib.import_module('MainGame.src.shop')
    print('OK')
except Exception as e:
    print('IMPORT_ERROR:', e)
    raise
