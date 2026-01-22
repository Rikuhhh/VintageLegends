"""
Test script to demonstrate the new percentage-based defense system
with soft/hard caps and penetration mechanics.
"""

def calculate_effective_stat(raw_value, soft_cap, hard_cap):
    """Calculate effective stat with soft and hard caps."""
    if raw_value <= soft_cap:
        return raw_value
    elif raw_value <= hard_cap:
        excess = raw_value - soft_cap
        return soft_cap + (excess * 0.5)
    else:
        excess = hard_cap - soft_cap
        return soft_cap + (excess * 0.5)

def test_defense_examples():
    print("=" * 60)
    print("DEFENSE SYSTEM TEST - Percentage-based with Soft/Hard Caps")
    print("=" * 60)
    
    # Test various defense values
    test_cases = [
        (0, "No defense"),
        (15, "Low defense"),
        (30, "At soft cap"),
        (40, "Above soft cap (diminishing)"),
        (60, "Well above soft cap"),
        (75, "At hard cap"),
        (100, "Above hard cap (capped)"),
    ]
    
    print("\nDEFENSE EFFECTIVENESS:")
    print("-" * 60)
    for def_value, desc in test_cases:
        effective = calculate_effective_stat(def_value, 30, 75)
        print(f"{def_value:3d} DEF ({desc:25s}) = {effective:5.1f}% damage reduction")
    
    # Test penetration
    print("\n\nPENETRATION EFFECTIVENESS:")
    print("-" * 60)
    pen_cases = [
        (0, "No penetration"),
        (25, "Low penetration"),
        (50, "At soft cap"),
        (60, "Above soft cap (diminishing)"),
        (75, "At hard cap"),
        (100, "Above hard cap (capped)"),
    ]
    
    for pen_value, desc in pen_cases:
        effective = calculate_effective_stat(pen_value, 50, 75)
        print(f"{pen_value:3d} PEN ({desc:25s}) = {effective:5.1f}% defense ignored")
    
    # Test penetration vs defense interactions
    print("\n\nPENETRATION vs DEFENSE INTERACTIONS:")
    print("-" * 60)
    print("Format: [DEF] vs [PEN] = Effective Defense%")
    print("-" * 60)
    
    interactions = [
        (75, 0, "Max defense vs no penetration"),
        (75, 50, "Max defense vs soft-cap penetration"),
        (75, 75, "Max defense vs max penetration"),
        (30, 25, "Soft-cap defense vs low penetration"),
        (100, 100, "Overcapped both"),
    ]
    
    for def_val, pen_val, desc in interactions:
        def_eff = calculate_effective_stat(def_val, 30, 75)
        pen_eff = calculate_effective_stat(pen_val, 50, 75)
        final_def = def_eff * (1.0 - (pen_eff / 100.0))
        print(f"{def_val:3d} DEF vs {pen_val:3d} PEN: {final_def:5.1f}% reduction ({desc})")
    
    # Damage calculation examples
    print("\n\nDAMAGE CALCULATION EXAMPLES:")
    print("-" * 60)
    print("Incoming damage: 100")
    print("-" * 60)
    
    damage_cases = [
        (0, 0, "No defense, no penetration"),
        (30, 0, "30 DEF (30% reduction - soft cap)"),
        (60, 0, "60 DEF (52.5% reduction)"),
        (75, 0, "75 DEF (52.5% reduction - hard cap)"),
        (100, 0, "100 DEF (52.5% reduction - capped)"),
        (75, 50, "75 DEF vs 50 PEN"),
        (75, 75, "75 DEF vs 75 PEN"),
    ]
    
    base_dmg = 100
    for def_val, pen_val, desc in damage_cases:
        def_eff = calculate_effective_stat(def_val, 30, 75)
        pen_eff = calculate_effective_stat(pen_val, 50, 75) if pen_val > 0 else 0
        final_def = def_eff * (1.0 - (pen_eff / 100.0))
        dmg_taken = max(1, int(base_dmg * (1.0 - final_def / 100.0)))
        print(f"{desc:40s} = {dmg_taken:3d} damage taken")
    
    print("\n" + "=" * 60)
    print("KEY INSIGHTS:")
    print("=" * 60)
    print("• Defense: Soft cap at 30% (1:1), Hard cap at 75% (diminishing)")
    print("• Penetration: Soft cap at 50% (1:1), Hard cap at 75% (diminishing)")
    print("• Penetration REDUCES defense effectiveness multiplicatively")
    print("• Example: 50% pen vs 52.5% def = 52.5% * 0.5 = 26.25% final reduction")
    print("• All damage has minimum of 1 (can't fully negate)")
    print("• Hard cap at 75 DEF gives 52.5% reduction (never reaches 75%)")
    print("=" * 60)

if __name__ == "__main__":
    test_defense_examples()
