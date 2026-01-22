"""Test the new equipment system with multiple slots"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from player import Player

# Create a test player
data = {
    'name': 'Test Hero',
    'hp': 100,
    'max_hp': 100,
    'atk': 10,
    'defense': 5,
    'gold': 1000,
    'xp': 0,
    'level': 1
}

player = Player(data)

print("=== Equipment System Test ===\n")
print(f"Initial stats:")
print(f"  HP: {player.hp}/{player.max_hp}")
print(f"  ATK: {player.atk}")
print(f"  DEF: {player.defense}")
print(f"  PEN: {player.penetration}")
print(f"  Crit Chance: {player.critchance}")
print(f"  Crit Damage: {player.critdamage}")

print(f"\nEquipment slots: {list(player.equipment.keys())}")
print(f"All slots empty: {all(v is None for v in player.equipment.values())}")

# Test adding items
print("\n=== Testing Item Addition ===")

# Add weapon
weapon = {'id': 'iron_sword', 'name': 'Iron Sword', 'type': 'weapon', 'attack': 15, 'penetration': 5}
player.add_item(weapon, auto_equip=True)
print(f"\nAdded Iron Sword:")
print(f"  Weapon slot: {player.equipment['weapon']}")
print(f"  ATK: {player.atk} (should be 25 = 10 base + 15 weapon)")
print(f"  PEN: {player.penetration} (should be 5)")

# Add armor
armor = {'id': 'steel_armor', 'name': 'Steel Armor', 'type': 'armor', 'defense': 20}
player.add_item(armor, auto_equip=True)
print(f"\nAdded Steel Armor:")
print(f"  Armor slot: {player.equipment['armor']}")
print(f"  DEF: {player.defense} (should be 25 = 5 base + 20 armor)")

# Add offhand
offhand = {'id': 'iron_shield', 'name': 'Iron Shield', 'type': 'offhand', 'defense': 12, 'max_hp': 20}
player.add_item(offhand, auto_equip=True)
print(f"\nAdded Iron Shield:")
print(f"  Offhand slot: {player.equipment['offhand']}")
print(f"  DEF: {player.defense} (should be 37 = 5 base + 20 armor + 12 shield)")
print(f"  Max HP: {player.max_hp} (should be 120 = 100 base + 20 shield)")

# Add relics
relic1 = {'id': 'power_ring', 'name': 'Power Ring', 'type': 'relic', 'attack': 10}
player.add_item(relic1, auto_equip=True)
print(f"\nAdded Power Ring (Relic 1):")
print(f"  Relic1 slot: {player.equipment['relic1']}")
print(f"  ATK: {player.atk} (should be 35 = 10 base + 15 weapon + 10 relic)")

relic2 = {'id': 'vitality_amulet', 'name': 'Vitality Amulet', 'type': 'relic', 'max_hp': 50, 'defense': 5}
player.add_item(relic2, auto_equip=True)
print(f"\nAdded Vitality Amulet (Relic 2):")
print(f"  Relic2 slot: {player.equipment['relic2']}")
print(f"  DEF: {player.defense} (should be 42 = 5 base + 20 armor + 12 shield + 5 amulet)")
print(f"  Max HP: {player.max_hp} (should be 170 = 100 base + 20 shield + 50 amulet)")

relic3 = {'id': 'critical_charm', 'name': 'Critical Charm', 'type': 'relic', 'critchance': 0.15, 'critdamage': 0.3}
player.add_item(relic3, auto_equip=True)
print(f"\nAdded Critical Charm (Relic 3):")
print(f"  Relic3 slot: {player.equipment['relic3']}")
print(f"  Crit Chance: {player.critchance} (should be 0.15)")
print(f"  Crit Damage: {player.critdamage} (should be 1.8 = 1.5 base + 0.3)")

# Test unequipping
print("\n=== Testing Unequip ===")
player.unequip('relic2')
print(f"Unequipped Vitality Amulet:")
print(f"  Relic2 slot: {player.equipment['relic2']} (should be None)")
print(f"  DEF: {player.defense} (should be 37 = 5 base + 20 armor + 12 shield)")
print(f"  Max HP: {player.max_hp} (should be 120 = 100 base + 20 shield)")
print(f"  Inventory has vitality_amulet: {player.has_item('vitality_amulet')}")

# Test relic slot overflow
print("\n=== Testing Relic Overflow (all 3 slots full) ===")
player.add_item(relic2, auto_equip=True)  # Re-add to relic2
relic4 = {'id': 'dragon_eye', 'name': 'Dragon Eye', 'type': 'relic', 'attack': 15}
player.add_item(relic4, auto_equip=True)  # Should go to inventory since all relic slots full
print(f"Tried to add 4th relic (Dragon Eye):")
print(f"  Relic slots: {[player.equipment[f'relic{i}'] for i in [1,2,3]]}")
print(f"  Dragon Eye in inventory: {player.has_item('dragon_eye')}")

print("\n=== Final Equipment Summary ===")
for slot, item_id in player.equipment.items():
    print(f"  {slot}: {item_id or 'Empty'}")

print(f"\n=== Final Stats ===")
print(f"  HP: {player.hp}/{player.max_hp}")
print(f"  ATK: {player.atk}")
print(f"  DEF: {player.defense}")
print(f"  PEN: {player.penetration}")
print(f"  Crit Chance: {player.critchance}")
print(f"  Crit Damage: {player.critdamage}")
print(f"\n✓ Equipment system test complete!")
