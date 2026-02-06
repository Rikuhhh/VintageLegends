# Crafting System

## Overview
The crafting system allows players to combine materials and items to create new items. Players can access the crafting UI by pressing the **R** key or clicking the "Crafting (R)" button in the main UI.

## Features

### For Players
- **Crafting UI**: A responsive, full-screen modal interface showing all available recipes
- **Recipe Browser**: Browse all recipes categorized by type (weapon, armor, consumable, material, misc)
- **Real-time Requirements**: See exactly which ingredients you need and which you have
- **Level Requirements**: Some recipes require minimum player levels
- **Visual Feedback**: Clear indicators showing which recipes you can craft
- **One-Click Crafting**: Craft items with a single click when you have all ingredients

### For Admins
- **Recipe Manager**: Dedicated "Recipes" tab in the admin interface
- **Easy Creation**: Add new recipes with a simple form interface
- **Ingredient Management**: Add/remove ingredients dynamically
- **Full Control**: Edit all recipe properties including:
  - Recipe ID, name, and description
  - Result item and quantity
  - Required ingredients and quantities
  - Minimum player level
  - Recipe category

## How to Use (Players)

1. **Open Crafting UI**: Press **R** key or click "Crafting (R)" button
2. **Browse Recipes**: Click on any recipe in the left panel to view details
3. **Check Requirements**: 
   - Green checkmark = You can craft this recipe
   - Red X = Missing ingredients or level too low
4. **Craft Item**: Click the "CRAFT" button when requirements are met
5. **Receive Item**: Crafted items are added to your inventory automatically

## How to Create Recipes (Admins)

1. **Open Admin Interface**: Run `python3 tools/admin_interface.py`
2. **Go to Recipes Tab**: Click on the "Recipes" tab
3. **Create New Recipe**:
   - Click "New Recipe" button
   - Fill in required fields (ID, Name, Result Item ID, Category)
   - Click "Add Ingredient" for each required material
   - Enter ingredient item IDs and quantities
   - Set optional fields (description, required level, result quantity)
   - Click "Save Recipe"

## Recipe Data Structure

Recipes are stored in `data/recipes.json`:

```json
{
  "recipes": [
    {
      "id": "health_potion",
      "name": "Health Potion",
      "description": "Craft a basic health potion",
      "result_item_id": "potion_health",
      "result_quantity": 1,
      "ingredients": [
        {
          "item_id": "herb_healing",
          "quantity": 2
        },
        {
          "item_id": "water_crystal",
          "quantity": 1
        }
      ],
      "required_level": 1,
      "category": "consumable"
    }
  ]
}
```

## Recipe Categories

- **weapon**: Recipes for crafting weapons
- **armor**: Recipes for crafting armor pieces
- **consumable**: Recipes for potions, food, and consumables
- **material**: Recipes for processing raw materials
- **misc**: Other recipes

## Example Recipes

### Health Potion
- **Ingredients**: 2x Healing Herb, 1x Water Crystal
- **Result**: 1x Health Potion (restores 50 HP)
- **Level Required**: 1

### Iron Sword
- **Ingredients**: 3x Iron Ore, 1x Wood Plank
- **Result**: 1x Iron Sword (+25 Attack)
- **Level Required**: 3

## UI Responsiveness

The crafting UI is fully responsive and adapts to different screen sizes:
- **Large Modal**: 900x600 pixel centered window
- **Two-Panel Layout**: Recipe list on left, details on right
- **Scrollable Lists**: Long recipe lists scroll smoothly
- **Visual Categories**: Color-coded recipe categories
- **Status Indicators**: Clear visual feedback for craftable/non-craftable recipes

## Technical Details

### Files
- `src/crafting_system.py`: Core crafting logic
- `src/ui_manager.py`: Crafting UI rendering (method `_draw_crafting_ui`)
- `data/recipes.json`: Recipe definitions
- `data_schemas/recipes.schema.json`: JSON schema for validation
- `tools/admin_interface.py`: Recipe management UI

### Key Methods

**CraftingSystem**:
- `get_all_recipes()`: Get all available recipes
- `can_craft(recipe_id, inventory, level)`: Check if player can craft
- `craft_item(recipe_id, inventory, level)`: Attempt to craft an item
- `get_available_recipes(inventory, level)`: Get craftable recipes

**UI Manager**:
- `_draw_crafting_ui(player, battle)`: Render the crafting interface
- Integrated with existing event handling system
- Hotkey: **R** key toggles crafting UI

## Future Enhancements

Potential features for future updates:
- Recipe discovery system (unlock recipes by finding scrolls)
- Crafting professions (blacksmithing, alchemy, etc.)
- Quality tiers (normal, rare, epic crafted items)
- Batch crafting (craft multiple items at once)
- Crafting animations and sound effects
- Recipe sorting and filtering
- Search functionality for recipes
