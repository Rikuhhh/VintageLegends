"""Developer data editor (terminal) for adding/editing/listing data files.

Usage:
  python tools/edit_data.py --file items.json

Features:
- List entries (id and name where present)
- Add a new entry using your system editor (Notepad on Windows)
- Edit an existing entry in your editor
- Delete an entry (with confirmation)
- Validates data using schemas in ../data_schemas before saving
- Atomic save with timestamped backup

This is a safe dev interface intended for local developers.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from jsonschema import Draft7Validator
except Exception:
    print('jsonschema not installed. Run: pip install jsonschema')
    sys.exit(2)

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data'
SCHEMAS = BASE / 'data_schemas'

MAPPING = {
    'items.json': 'items.schema.json',
    'monsters.json': 'monsters.schema.json',
    'attacks.json': 'attacks.schema.json',
    'upgrades.json': 'upgrades.schema.json',
    'characters.json': 'characters.schema.json',
}

EDITOR = os.environ.get('EDITOR') or 'notepad'


def load_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_atomic(path: Path, data):
    # backup
    if path.exists():
        bak_name = f"{path.name}.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        bak_path = path.parent / bak_name
        shutil.copy2(path, bak_path)
        print(f"Backup created: {bak_path}")
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, path)
    print(f"Saved {path}")


def validate_data(fname: str, data) -> list:
    schema_name = MAPPING.get(fname)
    if not schema_name:
        return [f'No schema mapping for {fname}']
    schema_path = SCHEMAS / schema_name
    if not schema_path.exists():
        return [f'Schema missing: {schema_path}']
    with open(schema_path, 'r', encoding='utf-8') as s:
        schema = json.load(s)
    v = Draft7Validator(schema)
    errors = list(v.iter_errors(data))
    return errors


def open_in_editor(initial: str) -> str:
    fd, tmp = tempfile.mkstemp(suffix='.json', text=True)
    os.close(fd)
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(initial)
    # open editor and wait
    try:
        subprocess.run([EDITOR, tmp], check=True)
    except Exception:
        # fallback to system default
        if sys.platform == 'win32':
            os.startfile(tmp)
        elif sys.platform == 'darwin':
            subprocess.run(['open', tmp])
        else:
            subprocess.run(['xdg-open', tmp])
    with open(tmp, 'r', encoding='utf-8') as f:
        out = f.read()
    os.remove(tmp)
    return out


def pretty(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', '-f', required=True, help='data filename under data/ (e.g. items.json)')
    args = ap.parse_args()

    fname = args.file
    data_path = DATA / fname
    if not data_path.exists():
        print(f'File not found: {data_path}')
        sys.exit(1)
    try:
        data = load_json(data_path)
    except Exception as e:
        print('Failed to load JSON:', e)
        sys.exit(1)

    schema_name = MAPPING.get(fname)
    if not schema_name:
        print('No schema registered for this file, aborting.')
        sys.exit(1)

    # data container assumed to contain a top-level array under a key (items/enemies/attacks/upgrades/characters)
    top_keys = list(data.keys())
    if not top_keys:
        print('Data file invalid: no top-level keys')
        sys.exit(1)
    top_key = top_keys[0]
    arr = data.get(top_key, [])

    while True:
        print('\nDeveloper editor -', fname)
        print('Top key:', top_key)
        print('[L]ist entries  [A]dd  [E]dit  [D]elete  [V]alidate  [Q]uit')
        cmd = input('> ').strip().lower()
        if cmd == 'l':
            for i, entry in enumerate(arr):
                eid = entry.get('id', '<no id>')
                name = entry.get('name', '')
                print(f'[{i}] {eid} - {name}')
        elif cmd == 'a':
            print('Creating new entry. A temp file will open in', EDITOR)
            # prepare skeleton
            skeleton = {}
            # if schema exists, try to include required fields with placeholders
            schema_path = SCHEMAS / schema_name
            with open(schema_path, 'r', encoding='utf-8') as s:
                schema = json.load(s)
            # attempt to extract item schema at items.items.items
            item_schema = None
            # for items.json the path is schema['properties'][top_key]['items']
            try:
                item_schema = schema['properties'][top_key]['items']
            except Exception:
                item_schema = None
            if item_schema:
                reqs = item_schema.get('required', [])
                for r in reqs:
                    skeleton[r] = f'<{r}>'
            else:
                skeleton = {'id': '<id>', 'name': '<name>'}
            body = '{\n' + pretty(skeleton) + '\n}\n'
            edited = open_in_editor(body)
            try:
                obj = json.loads(edited)
            except Exception as e:
                print('Invalid JSON:', e)
                continue
            # append and validate full document
            arr.append(obj)
            data[top_key] = arr
            v_errs = validate_data(fname, data)
            if v_errs:
                print('Validation failed:')
                for ve in v_errs:
                    print(' -', getattr(ve, 'message', str(ve)))
                # rollback
                arr.pop()
            else:
                write_atomic(data_path, data)
        elif cmd == 'e':
            idx = input('Entry index to edit: ').strip()
            if not idx.isdigit() or int(idx) < 0 or int(idx) >= len(arr):
                print('Invalid index')
                continue
            idx = int(idx)
            initial = pretty(arr[idx])
            edited = open_in_editor(initial)
            try:
                obj = json.loads(edited)
            except Exception as e:
                print('Invalid JSON:', e)
                continue
            arr[idx] = obj
            data[top_key] = arr
            v_errs = validate_data(fname, data)
            if v_errs:
                print('Validation failed:')
                for ve in v_errs:
                    print(' -', getattr(ve, 'message', str(ve)))
                print('Changes not saved.')
            else:
                write_atomic(data_path, data)
        elif cmd == 'd':
            idx = input('Entry index to delete: ').strip()
            if not idx.isdigit() or int(idx) < 0 or int(idx) >= len(arr):
                print('Invalid index')
                continue
            idx = int(idx)
            eid = arr[idx].get('id', '<no id>')
            ok = input(f'Confirm delete {eid}? (y/N): ').strip().lower()
            if ok == 'y':
                arr.pop(idx)
                data[top_key] = arr
                write_atomic(data_path, data)
        elif cmd == 'v':
            v_errs = validate_data(fname, data)
            if v_errs:
                print('Validation issues:')
                for ve in v_errs:
                    print(' -', getattr(ve, 'message', str(ve)))
            else:
                print('No validation errors.')
        elif cmd == 'q':
            print('Bye')
            break
        else:
            print('Unknown command')


if __name__ == '__main__':
    main()
