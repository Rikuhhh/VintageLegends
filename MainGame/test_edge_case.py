"""Edge case test: Player at full HP"""
import sys
from pathlib import Path

src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from player import Player

def test_full_hp_allocation():
    """Test HP allocation when player is at full health"""
    print("\n=== Test: HP allocation when at full health ===")
    
    player_data = {
        "name": "FullHP",
        "hp": 100,
        "atk": 10,
        "def": 5,
        "unspent_points": 3
    }
    
    player = Player(player_data)
    print(f"Initial: HP = {player.hp}/{player.max_hp}")
    
    # Player is at full HP
    assert player.hp == player.max_hp
    
    # Spend HP point
    player.spend_point("hp")
    print(f"After HP point: HP = {player.hp}/{player.max_hp}")
    
    # Should still be at full HP (100/105) - not healed to 105
    assert player.hp == 100, f"HP changed to {player.hp}, expected 100"
    assert player.max_hp == 105, f"max_hp is {player.max_hp}, expected 105"
    
    print("✓ PASS: Player at full HP before allocation stays at same current HP value")
    
    # Now test when player is damaged
    player.hp = 50
    print(f"\nAfter damage: HP = {player.hp}/{player.max_hp}")
    
    player.spend_point("hp")
    print(f"After HP point: HP = {player.hp}/{player.max_hp}")
    
    assert player.hp == 50, f"HP changed to {player.hp}, expected 50"
    assert player.max_hp == 110, f"max_hp is {player.max_hp}, expected 110"
    
    print("✓ PASS: Damaged player stays at same current HP value")

if __name__ == "__main__":
    test_full_hp_allocation()
    print("\n✅ Edge case test passed!")
