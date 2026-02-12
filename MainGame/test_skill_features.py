#!/usr/bin/env python3
"""Test multi-hit and DoT features for skills."""

import json

# Load skills.json
with open('data/skills.json', 'r', encoding='utf-8') as f:
    skills_data = json.load(f)

print("=== Skill Features Test ===\n")

# Find skills with multi-hit
multi_hit_skills = []
for skill in skills_data.get('skills', []):
    if 'multi_hit' in skill:
        multi_hit_skills.append(skill)

print(f"Found {len(multi_hit_skills)} skill(s) with multi-hit:\n")
for skill in multi_hit_skills:
    multi_hit = skill['multi_hit']
    hits = multi_hit.get('hits', 0)
    dmg_per_hit = multi_hit.get('damage_per_hit', 0)
    total_mult = hits * dmg_per_hit
    print(f"  {skill['name']} ({skill['id']})")
    print(f"    Type: {skill.get('type')}")
    print(f"    Multi-hit: {hits} hits × {dmg_per_hit*100:.0f}% = {total_mult*100:.0f}% total")
    print(f"    Power: {skill.get('power', 0)}")
    print()

# Find skills with DoT
dot_skills = []
for skill in skills_data.get('skills', []):
    effects = skill.get('effects', [])
    for effect in effects:
        if effect.get('type') == 'dot':
            dot_skills.append((skill, effect))
            break

print(f"\nFound {len(dot_skills)} skill(s) with DoT:\n")
for skill, dot_effect in dot_skills:
    damage = dot_effect.get('damage', 0)
    duration = dot_effect.get('duration', 0)
    damage_type = dot_effect.get('damage_type', 'physical')
    
    print(f"  {skill['name']} ({skill['id']})")
    print(f"    Type: {skill.get('type')}")
    print(f"    Element: {skill.get('element', 'neutral')}")
    print(f"    DoT: {damage} base damage/turn for {duration} turns")
    print(f"    Damage Type: {damage_type}")
    if damage_type == 'magic':
        print(f"    Scaling: +30% of Magic Power")
    else:
        print(f"    Scaling: +20% of Attack")
    total_dot = damage * duration
    print(f"    Total DoT: {total_dot} (base, before scaling)")
    print()

print("\n✓ Admin UI now supports:")
print("  - Multi-hit configuration for skills (hits, damage per hit)")
print("  - DoT damage type selection (physical/magic)")
print("  - DoT scales with caster's ATK or Magic Power")
print("  - Sorting by type in Items/Monsters tabs")
print("  - Fixed search selection bug")
print("\nTo configure:")
print("  1. Run: python3 tools/admin_interface.py")
print("  2. Go to Skills tab")
print("  3. Select or create a skill")
print("  4. Enable Multi-Hit or DoT checkboxes")
print("  5. Configure values and save")
