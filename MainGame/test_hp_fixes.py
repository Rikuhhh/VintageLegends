"""Test script to verify HP bug fixes"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from player import Player

def test_hp_allocation_no_heal():
    """Test that allocating HP points doesn't heal the player"""
    print("\n=== Test 1: HP point allocation should not heal ===")
    
    # Create player with 100 HP
    player_data = {
        "name": "TestHero",
        "hp": 100,
        "atk": 10,
        "def": 5,
        "unspent_points": 3
    }
    player = Player(player_data)
    
    # Damage the player
    player.hp = 50  # Player is at half health
    print(f"Initial: HP = {player.hp}/{player.max_hp}")
    
    # Spend HP point (should increase max_hp but NOT heal)
    player.spend_point("hp")
    print(f"After HP point: HP = {player.hp}/{player.max_hp}")
    
    if player.hp == 50:
        print("✓ PASS: HP stayed at 50 (no healing)")
    else:
        print(f"✗ FAIL: HP changed to {player.hp} (expected 50)")
    
    if player.max_hp == 105:
        print("✓ PASS: max_hp increased by 5")
    else:
        print(f"✗ FAIL: max_hp is {player.max_hp} (expected 105)")

def test_non_hp_allocation_preserves_bonuses():
    """Test that allocating non-HP points preserves challenge/upgrade HP bonuses"""
    print("\n=== Test 2: Non-HP allocation should preserve HP bonuses ===")
    
    # Create player with challenge upgrade
    player_data = {
        "name": "TestHero",
        "hp": 100,
        "atk": 10,
        "def": 5,
        "unspent_points": 3,
        "permanent_upgrades": {
            "hp_boost": 2  # +20 HP from challenge upgrade (2 levels * 10 HP)
        }
    }
    player = Player(player_data)
    
    # Force recalc to apply upgrades
    player._recalc_stats()
    
    print(f"Initial: HP = {player.hp}/{player.max_hp} (base + 20 from upgrades)")
    initial_max_hp = player.max_hp
    
    # Spend ATK point (should NOT remove HP bonuses)
    player.spend_point("atk")
    print(f"After ATK point: HP = {player.hp}/{player.max_hp}")
    
    if player.max_hp == initial_max_hp:
        print(f"✓ PASS: max_hp preserved at {player.max_hp} (bonuses kept)")
    else:
        print(f"✗ FAIL: max_hp changed from {initial_max_hp} to {player.max_hp}")
    
    # Spend DEF point
    player.spend_point("def")
    print(f"After DEF point: HP = {player.hp}/{player.max_hp}")
    
    if player.max_hp == initial_max_hp:
        print(f"✓ PASS: max_hp still preserved at {player.max_hp}")
    else:
        print(f"✗ FAIL: max_hp changed from {initial_max_hp} to {player.max_hp}")

def test_combined_scenario():
    """Test a combined scenario with equipment and upgrades"""
    print("\n=== Test 3: Combined scenario with equipment + upgrades ===")
    
    player_data = {
        "name": "TestHero",
        "hp": 100,
        "atk": 10,
        "def": 5,
        "unspent_points": 5,
        "permanent_upgrades": {
            "hp_boost": 3  # +30 HP from challenge
        },
        "equipment": {
            "weapon": None,
            "armor": None,
            "offhand": None,
            "relic1": None,
            "relic2": None,
            "relic3": None
        }
    }
    player = Player(player_data)
    player._recalc_stats()
    
    print(f"Starting: HP = {player.hp}/{player.max_hp}")
    print(f"Base stats: ATK={player.atk}, DEF={player.defense}")
    
    # Take some damage
    player.hp = 80
    print(f"After damage: HP = {player.hp}/{player.max_hp}")
    
    # Spend various points
    player.spend_point("atk")
    print(f"After ATK: HP = {player.hp}/{player.max_hp}, ATK={player.atk}")
    
    player.spend_point("def")
    print(f"After DEF: HP = {player.hp}/{player.max_hp}, DEF={player.defense}")
    
    player.spend_point("hp")
    print(f"After HP: HP = {player.hp}/{player.max_hp}")
    
    # Verify HP stayed at 80 (no healing)
    if player.hp == 80:
        print("✓ PASS: Current HP preserved at 80 through all allocations")
    else:
        print(f"✗ FAIL: Current HP changed to {player.hp} (expected 80)")
    
    # Verify max_hp increased correctly (base 100 + 30 from upgrade + 5 from point)
    expected_max = 135
    if player.max_hp == expected_max:
        print(f"✓ PASS: max_hp is {player.max_hp} (100 base + 30 upgrade + 5 point)")
    else:
        print(f"✗ FAIL: max_hp is {player.max_hp} (expected {expected_max})")

if __name__ == "__main__":
    print("Testing HP allocation bug fixes...")
    print("=" * 60)
    
    test_hp_allocation_no_heal()
    test_non_hp_allocation_preserves_bonuses()
    test_combined_scenario()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
