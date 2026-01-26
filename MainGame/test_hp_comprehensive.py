"""Final comprehensive test of HP mechanics"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from player import Player

def test_complete_workflow():
    """Test a complete workflow with all scenarios"""
    print("\n=== Complete Workflow Test ===")
    
    player_data = {
        "name": "Hero",
        "hp": 100,
        "atk": 10,
        "def": 5,
        "xp": 0,
        "level": 1,
        "unspent_points": 0,
        "permanent_upgrades": {
            "hp_boost": 2  # +20 HP
        }
    }
    
    player = Player(player_data)
    player._recalc_stats()
    
    print(f"Level {player.level}: HP = {player.hp}/{player.max_hp}")
    print(f"Base max_hp: {player.base_max_hp}")
    
    # Take damage
    player.hp = 80
    print(f"\nAfter taking damage: HP = {player.hp}/{player.max_hp}")
    
    # Simulate gaining points from somewhere
    player.unspent_points = 5
    
    # Test 1: Spend ATK point (should not affect HP)
    print(f"\n--- Spending ATK point ---")
    prev_hp = player.hp
    prev_max = player.max_hp
    player.spend_point("atk")
    print(f"HP: {player.hp}/{player.max_hp} (was {prev_hp}/{prev_max})")
    assert player.hp == prev_hp, f"ATK point changed HP from {prev_hp} to {player.hp}!"
    assert player.max_hp == prev_max, f"ATK point changed max_hp from {prev_max} to {player.max_hp}!"
    
    # Test 2: Spend DEF point (should not affect HP)
    print(f"\n--- Spending DEF point ---")
    prev_hp = player.hp
    prev_max = player.max_hp
    player.spend_point("def")
    print(f"HP: {player.hp}/{player.max_hp} (was {prev_hp}/{prev_max})")
    assert player.hp == prev_hp, f"DEF point changed HP from {prev_hp} to {player.hp}!"
    assert player.max_hp == prev_max, f"DEF point changed max_hp from {prev_max} to {player.max_hp}!"
    
    # Test 3: Spend HP point (should increase max but NOT heal)
    print(f"\n--- Spending HP point ---")
    prev_hp = player.hp
    prev_max = player.max_hp
    player.spend_point("hp")
    print(f"HP: {player.hp}/{player.max_hp} (was {prev_hp}/{prev_max})")
    assert player.hp == prev_hp, f"HP point healed from {prev_hp} to {player.hp}!"
    assert player.max_hp == prev_max + 5, f"HP point didn't increase max_hp correctly!"
    
    # Test 4: Spend AGI point (should not affect HP)
    print(f"\n--- Spending AGI point ---")
    prev_hp = player.hp
    prev_max = player.max_hp
    player.spend_point("agi")
    print(f"HP: {player.hp}/{player.max_hp} (was {prev_hp}/{prev_max})")
    assert player.hp == prev_hp, f"AGI point changed HP from {prev_hp} to {player.hp}!"
    assert player.max_hp == prev_max, f"AGI point changed max_hp from {prev_max} to {player.max_hp}!"
    
    # Verify final state
    print(f"\n--- Final State ---")
    print(f"HP: {player.hp}/{player.max_hp}")
    print(f"Base max_hp: {player.base_max_hp}")
    print(f"ATK: {player.atk}, DEF: {player.defense}, AGI: {player.agility}")
    print(f"Unspent points: {player.unspent_points}")
    
    # Expected: base 100 + 20 (upgrade) + 5 (hp point) = 125
    expected_max_hp = 125
    assert player.max_hp == expected_max_hp, f"Final max_hp is {player.max_hp}, expected {expected_max_hp}"
    assert player.hp == 80, f"Final HP is {player.hp}, expected 80 (no healing)"
    
    print("\n✓ All assertions passed!")

def test_challenge_hp_preservation():
    """Test that challenge HP bonuses are preserved through stat allocation"""
    print("\n=== Challenge HP Preservation Test ===")
    
    # Create player with significant challenge bonuses
    player_data = {
        "name": "Veteran",
        "hp": 100,
        "atk": 10,
        "def": 5,
        "unspent_points": 10,
        "permanent_upgrades": {
            "hp_boost": 5  # +50 HP from challenges
        }
    }
    
    player = Player(player_data)
    player._recalc_stats()
    
    print(f"Initial max_hp: {player.max_hp} (100 base + 50 challenge)")
    expected_initial = 150
    assert player.max_hp == expected_initial, f"Initial max_hp is {player.max_hp}, expected {expected_initial}"
    
    # Take damage
    player.hp = 100
    
    # Spend 5 non-HP points
    for stat in ["atk", "def", "agi", "atk", "def"]:
        prev_max = player.max_hp
        player.spend_point(stat)
        assert player.max_hp == prev_max, f"Spending {stat} changed max_hp from {prev_max} to {player.max_hp}!"
        print(f"After {stat}: max_hp still {player.max_hp} ✓")
    
    # Spend 3 HP points
    for i in range(3):
        prev_max = player.max_hp
        prev_hp = player.hp
        player.spend_point("hp")
        assert player.max_hp == prev_max + 5, f"HP point #{i+1} didn't increase max_hp correctly"
        assert player.hp == prev_hp, f"HP point #{i+1} healed the player!"
        print(f"After HP point #{i+1}: max_hp = {player.max_hp}, hp = {player.hp} ✓")
    
    # Final check: 100 base + 50 challenge + 15 (3 HP points) = 165
    expected_final = 165
    assert player.max_hp == expected_final, f"Final max_hp is {player.max_hp}, expected {expected_final}"
    assert player.hp == 100, f"HP changed to {player.hp}, expected 100"
    
    print(f"\n✓ Challenge bonuses preserved! Final: {player.hp}/{player.max_hp}")

if __name__ == "__main__":
    print("Running comprehensive HP mechanics tests...")
    print("=" * 60)
    
    try:
        test_complete_workflow()
        test_challenge_hp_preservation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Both bugs are fixed:")
        print("  1. Spending non-HP points preserves challenge HP bonuses")
        print("  2. Spending HP points doesn't heal the player")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
