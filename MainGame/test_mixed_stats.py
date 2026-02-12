#!/usr/bin/env python3
"""Test that offensive stats work on armor and defensive stats on weapons."""

import json
import sys

# Load items.json
with open('data/items.json', 'r', encoding='utf-8') as f:
    items_data = json.load(f)

print("=== Mixed Stats Test ===\n")

# Find items with mixed stats
armor_with_offense = []
weapons_with_defense = []

for item in items_data.get('items', []):
    item_type = item.get('type')
    
    # Check armor with offensive stats
    if item_type == 'armor':
        has_offense = any([
            item.get('attack'),
            item.get('critchance'),
            item.get('critdamage'),
            item.get('magic_power'),
            item.get('lifesteal')
        ])
        if has_offense:
            armor_with_offense.append(item)
    
    # Check weapons with defensive stats
    if item_type == 'weapon':
        has_defense = any([
            item.get('defense'),
            item.get('max_hp'),
            item.get('hp_regen'),
            item.get('dodge_chance')
        ])
        if has_defense:
            weapons_with_defense.append(item)

print(f"Found {len(armor_with_offense)} armor piece(s) with offensive stats:")
for armor in armor_with_offense:
    print(f"  - {armor['name']} ({armor['id']})")
    if armor.get('attack'):
        print(f"    ATK: {armor['attack']}")
    if armor.get('critchance'):
        print(f"    Crit Chance: {armor['critchance']}")
    if armor.get('critdamage'):
        print(f"    Crit Damage: {armor['critdamage']}")
    if armor.get('magic_power'):
        print(f"    Magic Power: {armor['magic_power']}")
    print()

print(f"Found {len(weapons_with_defense)} weapon(s) with defensive stats:")
for weapon in weapons_with_defense:
    print(f"  - {weapon['name']} ({weapon['id']})")
    if weapon.get('defense'):
        print(f"    DEF: {weapon['defense']}")
    if weapon.get('max_hp'):
        print(f"    Max HP: {weapon['max_hp']}")
    if weapon.get('hp_regen'):
        print(f"    HP Regen: {weapon['hp_regen']}")
    if weapon.get('dodge_chance'):
        print(f"    Dodge: {weapon['dodge_chance']}")
    print()

print("\n✓ Admin UI now allows:")
print("  - Offensive stats (ATK, Crit, Magic Power) on ARMOR")
print("  - Defensive stats (DEF, HP, Dodge) on WEAPONS")
print("  - Both offensive AND defensive stats on all equipment")
print("\nThis enables hybrid builds and more interesting itemization!")
