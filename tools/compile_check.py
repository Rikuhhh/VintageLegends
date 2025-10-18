import py_compile
files = [
    r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends/MainGame/src/main.py',
    r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends/MainGame/src/modals.py',
    r'd:/Codage/CodeGeneral/CodePython/Personal/VintageLegends/MainGame/src/shop.py',
]
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print('OK', f)
    except Exception as e:
        print('ERROR', f, e)
        raise
