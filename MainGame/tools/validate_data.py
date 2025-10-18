"""Validate all data files in MainGame/data against the JSON schemas in data_schemas.

Usage:
    python tools/validate_data.py

Installs:
    pip install jsonschema
"""
from pathlib import Path
import json
import sys

try:
    from jsonschema import validate, Draft7Validator
    from jsonschema.exceptions import ValidationError
except Exception:
    print("jsonschema not installed. Run: pip install jsonschema")
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

errors = 0
for fname, sname in MAPPING.items():
    data_path = DATA / fname
    schema_path = SCHEMAS / sname
    if not data_path.exists():
        print(f"[SKIP] data file missing: {data_path}")
        continue
    if not schema_path.exists():
        print(f"[WARN] schema missing for {fname}: expected {schema_path}")
        continue
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse {data_path}: {e}")
        errors += 1
        continue
    try:
        with open(schema_path, 'r', encoding='utf-8') as s:
            schema = json.load(s)
    except Exception as e:
        print(f"[ERROR] Failed to parse schema {schema_path}: {e}")
        errors += 1
        continue
    validator = Draft7Validator(schema)
    v_errors = list(validator.iter_errors(data))
    if v_errors:
        print(f"[INVALID] {fname} has {len(v_errors)} validation errors:")
        for ve in v_errors:
            print(' -', ve.message)
        errors += 1
    else:
        print(f"[OK] {fname} matches {sname}")

if errors:
    print(f"\nValidation finished: {errors} file(s) invalid")
    sys.exit(1)
print("\nAll data files valid.")
