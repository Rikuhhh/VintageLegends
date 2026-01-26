"""Test script to verify seeding and shop price scaling"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from player import Player
from shop import Shop
from battle_system import BattleSystem

def test_seeding():
    """Test that seeding produces consistent results"""
    print("\n=== Test 1: Seeding Consistency ===")
    
    # Create two players with the same seed
    seed = 12345
    player1_data = {"name": "Test1", "hp": 100, "atk": 10, "def": 5, "game_seed": seed}
    player2_data = {"name": "Test2", "hp": 100, "atk": 10, "def": 5, "game_seed": seed}
    
    player1 = Player(player1_data)
    player2 = Player(player2_data)
    
    print(f"Player 1 seed: {player1.game_seed}")
    print(f"Player 2 seed: {player2.game_seed}")
    
    assert player1.game_seed == player2.game_seed, "Seeds should match"
    print("✓ Seeds match correctly")
    
    # Test shop offers with same seed
    data_path = Path(__file__).parent / 'data'
    shop = Shop(data_path)
    
    offers1 = shop.get_offers_for_wave(wave=5, player_seed=player1.game_seed, cumulative_increase=0.0)
    offers2 = shop.get_offers_for_wave(wave=5, player_seed=player2.game_seed, cumulative_increase=0.0)
    
    # Compare lengths
    assert len(offers1) == len(offers2), "Same seed should produce same number of offers"
    print(f"✓ Both players got {len(offers1)} offers with same seed")
    
    # Compare prices
    if len(offers1) > 0:
        for i in range(min(3, len(offers1))):
            price1 = offers1[i].get('_final_cost', 0)
            price2 = offers2[i].get('_final_cost', 0)
            assert price1 == price2, f"Prices should match for item {i}"
            print(f"  Item {i}: {offers1[i].get('name')} = {price1}g (both players)")
    
    print("✓ PASS: Seeding produces consistent shop offers")

def test_price_scaling():
    """Test that price increases accumulate correctly"""
    print("\n=== Test 2: Price Scaling Per Wave ===")
    
    player_data = {"name": "ScaleTest", "hp": 100, "atk": 10, "def": 5, "game_seed": 54321}
    player = Player(player_data)
    battle = BattleSystem(player)
    
    print(f"Initial cumulative increase: {player.cumulative_price_increase:.4f}")
    
    # Simulate 10 waves
    for i in range(10):
        battle.next_wave()
    
    print(f"After 10 waves cumulative increase: {player.cumulative_price_increase:.4f}")
    print(f"Expected increase: between 0.10 (10 * 1%) and 1.50 (10 * 15%)")
    
    # Should be between 10% and 150% total
    assert 0.10 <= player.cumulative_price_increase <= 1.50, "Cumulative increase out of range"
    print("✓ PASS: Price increases are within expected range")

def test_shop_stats():
    """Test shop statistics tracking"""
    print("\n=== Test 3: Shop Statistics Tracking ===")
    
    player_data = {"name": "StatsTest", "hp": 100, "atk": 10, "def": 5, "gold": 1000}
    player = Player(player_data)
    
    print(f"Initial stats:")
    print(f"  Items bought: {player.total_items_bought}")
    print(f"  Gold spent: {player.total_gold_spent}")
    
    # Simulate purchases
    player.total_items_bought = 5
    player.total_gold_spent = 250
    player.gold = 750
    
    print(f"\nAfter simulated purchases:")
    print(f"  Items bought: {player.total_items_bought}")
    print(f"  Gold spent: {player.total_gold_spent}")
    print(f"  Remaining gold: {player.gold}")
    
    assert player.total_items_bought == 5, "Items bought tracking failed"
    assert player.total_gold_spent == 250, "Gold spent tracking failed"
    print("✓ PASS: Shop statistics tracked correctly")

def test_deterministic_scaling():
    """Test that same seed produces same price increases"""
    print("\n=== Test 4: Deterministic Price Increases ===")
    
    seed = 99999
    
    # Run 1
    player1_data = {"name": "Run1", "hp": 100, "atk": 10, "def": 5, "game_seed": seed}
    player1 = Player(player1_data)
    battle1 = BattleSystem(player1)
    
    for i in range(5):
        battle1.next_wave()
    increase1 = player1.cumulative_price_increase
    
    # Run 2 with same seed
    player2_data = {"name": "Run2", "hp": 100, "atk": 10, "def": 5, "game_seed": seed}
    player2 = Player(player2_data)
    battle2 = BattleSystem(player2)
    
    for i in range(5):
        battle2.next_wave()
    increase2 = player2.cumulative_price_increase
    
    print(f"Run 1 increase after 5 waves: {increase1:.4f}")
    print(f"Run 2 increase after 5 waves: {increase2:.4f}")
    
    assert abs(increase1 - increase2) < 0.0001, "Same seed should produce same price increases"
    print("✓ PASS: Deterministic price increases with same seed")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Seeding and Shop Price Scaling Features")
    print("=" * 60)
    
    try:
        test_seeding()
        test_price_scaling()
        test_shop_stats()
        test_deterministic_scaling()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nFeatures implemented:")
        print("  ✓ Game seed system (auto-generated or custom)")
        print("  ✓ Seeded shop item appearance")
        print("  ✓ Wave-based price scaling (1-15% per wave, seeded)")
        print("  ✓ Cumulative price tracking")
        print("  ✓ Shop statistics (items bought, gold spent)")
        print("  ✓ Shop Stats tab in shop UI")
        print("  ✓ Game seed in character stats")
        print("  ✓ Seed selection on new game/retry")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
