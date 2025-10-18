import py_compile
files = [
    r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends/MainGame/src/player.py',
    r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends/MainGame/src/battle_system.py',
    r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends/MainGame/src/main.py'
]
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print('OK', f)
    except Exception as e:
        print('ERROR', f, e)
        raise
