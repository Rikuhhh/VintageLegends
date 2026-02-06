# Crafting UI Visual Guide

## Main Crafting Window Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CRAFTING                                                          [Close]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                    │                                         │
│  ┌─ RECIPES ─────────────────┐   │  ┌─ RECIPE DETAILS ──────────────────┐ │
│  │                            │   │  │                                    │ │
│  │ ┌────────────────────────┐ │   │  │  Iron Sword                        │ │
│  │ │ Health Potion          │ │   │  │  Forge a basic iron sword          │ │
│  │ │ CONSUMABLE             │ │   │  │  ────────────────────────────────  │ │
│  │ │ ✓ Can Craft            │ │   │  │                                    │ │
│  │ └────────────────────────┘ │   │  │  Required Ingredients:             │ │
│  │                            │   │  │   • Iron Ore: 3/3 ✓                │ │
│  │ ┌────────────────────────┐ │   │  │   • Wood Plank: 1/1 ✓              │ │
│  │ │ Iron Sword            ◄├─┼───┼─►│                                    │ │
│  │ │ WEAPON                 │ │   │  │  Result:                           │ │
│  │ │ ✓ Can Craft            │ │   │  │   Iron Sword x1                    │ │
│  │ └────────────────────────┘ │   │  │                                    │ │
│  │                            │   │  │  Required Level: 3                 │ │
│  │ ┌────────────────────────┐ │   │  │                                    │ │
│  │ │ Dragon Armor           │ │   │  │                                    │ │
│  │ │ ARMOR                  │ │   │  │                                    │ │
│  │ │ ✗ Need 5/8 scales      │ │   │  │                                    │ │
│  │ └────────────────────────┘ │   │  │                                    │ │
│  │                            │   │  │                                    │ │
│  │ ...                        │   │  │         ┌──────────────┐           │ │
│  │                            │   │  │         │    CRAFT     │           │ │
│  └────────────────────────────┘   │  │         └──────────────┘           │ │
│                                    │  └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Color Scheme

### Recipe List (Left Panel)
- **Background**: Dark gray (40, 40, 55)
- **Recipe boxes**:
  - Can craft: Green tint (60, 100, 60)
  - Cannot craft: Dark blue-gray (60, 60, 80)
  - Selected: Blue (80, 120, 160) with bright border

### Recipe Details (Right Panel)
- **Background**: Dark gray (40, 40, 55)
- **Recipe name**: Yellow (255, 255, 100)
- **Description**: Light gray (200, 200, 200)
- **Section headers**: Light blue (150, 200, 255)
- **Ingredients**:
  - Have enough: Green (100, 255, 100)
  - Missing: Red (255, 100, 100)
- **Result**: Yellow (255, 255, 150)
- **Craft button**:
  - Can craft: Green (80, 180, 80) - clickable
  - Cannot craft: Gray (80, 80, 80) - disabled

### Category Colors
- **WEAPON**: Orange-red (255, 150, 100)
- **ARMOR**: Blue (150, 200, 255)
- **CONSUMABLE**: Green (100, 255, 150)
- **MATERIAL**: Yellow (200, 200, 100)
- **MISC**: Gray (180, 180, 180)

## Button Location in Main UI

```
Main Game Screen Bottom Panel:
┌───────────────────────────────────────────┐
│                                           │
│   [Combat Log (L)]  ...  [Crafting (R)]   │
│                                           │
│          [Character (C)]  [Skills (K)]    │
└───────────────────────────────────────────┘
```

The "Crafting (R)" button is located:
- Bottom panel of the main UI
- Left side, next to Combat Log button
- Purple/violet color (180, 120, 200)
- Hotkey: R key

## Interaction Flow

1. **Opening**:
   - Click "Crafting (R)" button OR press R key
   - Modal window appears centered on screen

2. **Browsing**:
   - Scroll through recipe list on left
   - Click any recipe to view details
   - Selected recipe highlights with blue border

3. **Checking Requirements**:
   - Right panel shows all ingredients
   - Green text = you have enough
   - Red text = you're missing some
   - Status at top: "✓ Can Craft" or "✗ reason"

4. **Crafting**:
   - Click green "CRAFT" button
   - Ingredients consumed from inventory
   - Result item added to inventory
   - Combat log shows success message
   - UI updates to reflect new inventory

5. **Closing**:
   - Click "Close" button OR press R key again
   - Modal disappears, return to game

## Responsive Behavior

The UI automatically adapts:
- **Window size**: Fixed 900x600, centered on screen
- **Recipe list**: Scrolls if more recipes than fit
- **Long names**: Truncate with ellipsis (...)
- **Text wrapping**: Descriptions wrap at 50 characters
- **Ingredient list**: Each ingredient on new line
- **Button placement**: Always visible, bottom of detail panel

## Example States

### State 1: Can Craft
```
┌─ Recipe: Health Potion ──────────┐
│ Craft a basic health potion      │
│ ───────────────────────────────  │
│ Required Ingredients:             │
│  • Healing Herb: 2/2 ✓           │ (green)
│  • Water Crystal: 1/1 ✓          │ (green)
│                                   │
│ Result:                           │
│  Health Potion x1                 │
│                                   │
│     ┌──────────────┐              │
│     │    CRAFT     │ (green btn)  │
│     └──────────────┘              │
└───────────────────────────────────┘
```

### State 2: Missing Ingredients
```
┌─ Recipe: Iron Sword ─────────────┐
│ Forge a basic iron sword          │
│ ───────────────────────────────  │
│ Required Ingredients:             │
│  • Iron Ore: 1/3 ✗               │ (red)
│  • Wood Plank: 0/1 ✗             │ (red)
│                                   │
│ Result:                           │
│  Iron Sword x1                    │
│                                   │
│ Need 3x iron_ore (have 1)         │ (orange warning)
│     ┌──────────────┐              │
│     │CANNOT CRAFT  │ (gray btn)   │
│     └──────────────┘              │
└───────────────────────────────────┘
```

### State 3: Level Too Low
```
┌─ Recipe: Dragon Slayer ──────────┐
│ Legendary dragon-slaying sword    │
│ ───────────────────────────────  │
│ Required Ingredients:             │
│  • Dragon Scale: 5/5 ✓           │
│  • Mythril Ore: 10/10 ✓          │
│                                   │
│ Result:                           │
│  Dragon Slayer x1                 │
│                                   │
│ Required Level: 50                │ (red)
│ Requires level 50                 │ (orange warning)
│     ┌──────────────┐              │
│     │CANNOT CRAFT  │ (gray btn)   │
│     └──────────────┘              │
└───────────────────────────────────┘
```

## Admin Interface Layout

```
Admin Interface > Recipes Tab
┌────────────────────────────────────────────────────────────┐
│ ┌─ Existing Recipes ─┐  ┌─ Recipe Editor ────────────────┐│
│ │                     │  │                                ││
│ │ Health Potion       │  │ ID*:         [health_potion   ]││
│ │ Iron Sword          │  │ Name*:       [Health Potion   ]││
│ │ Dragon Armor        │  │ Description: [Craft potion... ]││
│ │ ...                 │  │ Category*:   [consumable ▼    ]││
│ │                     │  │ Result Item: [potion_health   ]││
│ │                     │  │ Result Qty:  [1               ]││
│ │                     │  │ Required Lvl:[1               ]││
│ │ [New Recipe]        │  │                                ││
│ │ [Delete]            │  │ ┌─ Ingredients ───────────────┐││
│ └─────────────────────┘  │ │ [Add Ingredient]            │││
│                          │ │                              │││
│                          │ │ Item ID: [herb_healing  ]    │││
│                          │ │ Qty:     [2             ]    │││
│                          │ │          [Remove]            │││
│                          │ │                              │││
│                          │ │ Item ID: [water_crystal ]    │││
│                          │ │ Qty:     [1             ]    │││
│                          │ │          [Remove]            │││
│                          │ └──────────────────────────────┘││
│                          │                                ││
│                          │         [Save Recipe]          ││
│                          └────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

---

This visual guide shows the complete UI layout and color scheme for the crafting system!
