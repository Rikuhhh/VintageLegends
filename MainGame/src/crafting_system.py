# src/crafting_system.py
import json
from pathlib import Path

class CraftingSystem:
    """Manages crafting recipes and crafting operations"""
    
    def __init__(self, data_path):
        """Initialize the crafting system
        
        Args:
            data_path: Path to the data directory containing recipes.json
        """
        self.data_path = Path(data_path)
        self.recipes = []
        self.load_recipes()
    
    def load_recipes(self):
        """Load recipes from recipes.json"""
        recipes_file = self.data_path / "recipes.json"
        if recipes_file.exists():
            try:
                with open(recipes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recipes = data.get('recipes', [])
                print(f"📜 Loaded {len(self.recipes)} crafting recipes")
            except Exception as e:
                print(f"Error loading recipes: {e}")
                self.recipes = []
        else:
            print("No recipes.json found, crafting system disabled")
            self.recipes = []
    
    def get_all_recipes(self):
        """Get all available recipes"""
        return self.recipes
    
    def get_recipe_by_id(self, recipe_id):
        """Get a specific recipe by ID
        
        Args:
            recipe_id: The recipe ID to search for
            
        Returns:
            Recipe dict or None if not found
        """
        for recipe in self.recipes:
            if recipe.get('id') == recipe_id:
                return recipe
        return None
    
    def get_recipes_by_category(self, category):
        """Get all recipes in a specific category
        
        Args:
            category: Category name (weapon, armor, consumable, etc.)
            
        Returns:
            List of recipes in that category
        """
        return [r for r in self.recipes if r.get('category') == category]
    
    def can_craft(self, recipe_id, player_inventory, player_level=1):
        """Check if a recipe can be crafted with current inventory
        
        Args:
            recipe_id: The recipe to check
            player_inventory: Dictionary of {item_id: quantity}
            player_level: Player's current level
            
        Returns:
            (bool, str): (can_craft, reason_if_not)
        """
        recipe = self.get_recipe_by_id(recipe_id)
        if not recipe:
            return False, "Recipe not found"
        
        # Check level requirement
        required_level = recipe.get('required_level', 1)
        if player_level < required_level:
            return False, f"Requires level {required_level}"
        
        # Check ingredients
        for ingredient in recipe.get('ingredients', []):
            item_id = ingredient.get('item_id')
            required_qty = ingredient.get('quantity', 1)
            
            current_qty = player_inventory.get(item_id, 0)
            if current_qty < required_qty:
                return False, f"Need {required_qty}x {item_id} (have {current_qty})"
        
        return True, "Can craft"
    
    def craft_item(self, recipe_id, player_inventory, player_level=1):
        """Attempt to craft an item
        
        Args:
            recipe_id: The recipe to craft
            player_inventory: Dictionary of {item_id: quantity} (will be modified)
            player_level: Player's current level
            
        Returns:
            (bool, str, result_item_id, result_quantity): (success, message, crafted_item_id, quantity)
        """
        can_craft, reason = self.can_craft(recipe_id, player_inventory, player_level)
        if not can_craft:
            return False, reason, None, 0
        
        recipe = self.get_recipe_by_id(recipe_id)
        
        # Remove ingredients from inventory
        for ingredient in recipe.get('ingredients', []):
            item_id = ingredient.get('item_id')
            required_qty = ingredient.get('quantity', 1)
            player_inventory[item_id] = player_inventory.get(item_id, 0) - required_qty
            
            # Remove item from inventory if quantity is 0
            if player_inventory[item_id] <= 0:
                del player_inventory[item_id]
        
        # Add result to inventory
        result_item_id = recipe.get('result_item_id')
        result_quantity = recipe.get('result_quantity', 1)
        
        player_inventory[result_item_id] = player_inventory.get(result_item_id, 0) + result_quantity
        
        return True, f"Crafted {result_quantity}x {recipe.get('name')}", result_item_id, result_quantity
    
    def get_available_recipes(self, player_inventory, player_level=1):
        """Get recipes that can be crafted with current resources
        
        Args:
            player_inventory: Dictionary of {item_id: quantity}
            player_level: Player's current level
            
        Returns:
            List of recipe IDs that can be crafted
        """
        available = []
        for recipe in self.recipes:
            can_craft, _ = self.can_craft(recipe.get('id'), player_inventory, player_level)
            if can_craft:
                available.append(recipe.get('id'))
        return available
