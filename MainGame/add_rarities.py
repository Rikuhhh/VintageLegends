#!/usr/bin/env python3
"""Add rarity field to all items in items.json"""
import json
from pathlib import Path

# Rarity assignment rules
def assign_rarity(item):
    """Assign rarity based on item properties"""
    item_id = item.get('id', '')
    name = item.get('name', '').lower()
    item_type = item.get('type', '')
    
    # Ancient - none for now
    
    # Mythical (red) - top tier items
    if any(word in item_id for word in ['legendary_lootbox', 'angelic_blade', 'moonlight_staff']):
        return 'mythical'
    
    # Legendary (gold) - very rare items
    if any(word in item_id for word in ['legendary_', 'phoenix', 'dragon_eye', 'demon_blade', 
                                         'void_dagger', 'infernal_armor', 'eldritch_tome']):
        return 'legendary'
    
    # Epic (purple) - rare items
    if any(word in item_id for word in ['mythril', 'shadow_', 'flame_', 'arcane_', 'dragon_', 
                                         'guardian_', 'vampiric', 'celestial', 'fey_lootbox',
                                         'infernal_lootbox', 'aberration_lootbox', 'hellfire_core',
                                         'void_crystal', 'holy_essence', 'starlight_shard']):
        return 'epic'
    
    # Rare (blue) - uncommon items
    if any(word in item_id for word in ['steel_', 'iron_chest', 'golden_chest', 'wizard_',
                                         'mage_', 'crystal_', 'enchanted_', 'greater_',
                                         'large_', 'elemental_', 'demon_horn', 'undead_essence',
                                         'ancient_rune', 'full_restore', 'infernal_steel',
                                         'mystery_lootbox', 'fey_dust', 'moonstone']):
        return 'rare'
    
    # Uncommon (green) - better than basic
    if any(word in item_id for word in ['iron_', 'medium_', 'spell_tome', 'power_ring',
                                         'vitality_amulet', 'critical_charm', 'penetration_relic',
                                         'balanced_talisman', 'mana_potion', 'elixir_',
                                         'aberrant_tissue', 'water_crystal', 'greatscraphammer']):
        return 'uncommon'
    
    # Common (white) - basic items
    return 'common'

def main():
    data_path = Path(__file__).parent / 'data' / 'items.json'
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items_updated = 0
    for item in data.get('items', []):
        if 'rarity' not in item:
            item['rarity'] = assign_rarity(item)
            items_updated += 1
            print(f"{item['id']:30s} -> {item['rarity']}")
    
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nUpdated {items_updated} items with rarities")

if __name__ == '__main__':
    main()
