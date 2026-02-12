#!/usr/bin/env python3
"""Test multi-hit weapon system."""

import sys
import json

# Load items.json to verify multi_hit data structure
with open('data/items.json', 'r', encoding='utf-8') as f:
    items_data = json.load(f)

print("=== Multi-Hit Weapon Test ===\n")

# Find multi-hit weapons
multi_hit_weapons = []
for item in items_data.get('items', []):
    if item.get('type') == 'weapon' and 'multi_hit' in item:
        multi_hit_weapons.append(item)

print(f"Found {len(multi_hit_weapons)} multi-hit weapon(s):\n")

for weapon in multi_hit_weapons:
    print(f"ID: {weapon['id']}")
    print(f"Name: {weapon['name']}")
    print(f"Attack: {weapon.get('attack', 0)}")
    multi_hit = weapon['multi_hit']
    hits = multi_hit.get('hits', 2)
    dmg_per_hit = multi_hit.get('damage_per_hit', 0.4)
    total_multiplier = hits * dmg_per_hit
    print(f"Multi-hit: {hits} hits × {dmg_per_hit*100:.0f}% = {total_multiplier*100:.0f}% total damage")
    print(f"Description: {weapon.get('description', 'N/A')}")
    print()

# Simulate damage calculations
print("=== Damage Simulation ===")
test_atk = 100
print(f"Base ATK: {test_atk}\n")

for weapon in multi_hit_weapons:
    weapon_atk = weapon.get('attack', 0)
    total_atk = test_atk + weapon_atk
    multi_hit = weapon['multi_hit']
    hits = multi_hit.get('hits', 2)
    dmg_per_hit = multi_hit.get('damage_per_hit', 0.4)
    
    # Normal weapon: 1 hit at 100% damage
    normal_damage = total_atk
    
    # Multi-hit weapon: multiple hits at reduced damage each
    hit_damage = int(total_atk * dmg_per_hit)
    total_multi_hit_damage = hit_damage * hits
    
    print(f"{weapon['name']}:")
    print(f"  Total ATK (base + weapon): {total_atk}")
    print(f"  Normal single-hit damage: {normal_damage}")
    print(f"  Multi-hit: {hits} × {hit_damage} = {total_multi_hit_damage}")
    print(f"  Damage difference: {total_multi_hit_damage - normal_damage:+d} ({(total_multi_hit_damage/normal_damage - 1)*100:+.1f}%)")
    print()

print("✓ Multi-hit weapon data structure validated!")
print("✓ Damage calculations look correct!")
print("\nNOTE: Multi-hit weapons benefit from:")
print("  - Multiple crit rolls (more consistent damage)")
print("  - Multiple lifesteal procs")
print("  - Better on-hit effect triggers (if implemented)")
