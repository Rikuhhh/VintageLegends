"""
Save Manager Tool - View, Modify, and Clear Save Files
"""
import json
import base64
from pathlib import Path
import sys

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

class SaveManagerTool:
    def __init__(self):
        self.save_dir = Path(__file__).parent.parent / "saves"
        self.save_file = self.save_dir / "save.save"
    
    def decode_save(self, encoded_data):
        """Decode save file"""
        try:
            decoded = base64.b64decode(encoded_data)
            return json.loads(decoded.decode('utf-8'))
        except Exception as e:
            print(f"Error decoding save: {e}")
            return None
    
    def encode_save(self, data):
        """Encode save data"""
        json_str = json.dumps(data, indent=4)
        return base64.b64encode(json_str.encode('utf-8'))
    
    def load_save(self):
        """Load and decode save file"""
        if not self.save_file.exists():
            print("❌ No save file found")
            return None
        
        with open(self.save_file, 'rb') as f:
            encoded = f.read()
        
        data = self.decode_save(encoded)
        if data:
            print("✅ Save file loaded successfully")
        return data
    
    def display_save(self, data):
        """Display save data in readable format"""
        if not data:
            return
        
        print("\n" + "="*60)
        print("SAVE FILE CONTENTS")
        print("="*60)
        print(f"Character: {data.get('name', 'Unknown')}")
        print(f"Level: {data.get('level', 1)}")
        print(f"HP: {data.get('hp', 0)} / {data.get('max_hp', 0)}")
        print(f"Gold: {data.get('gold', 0)}")
        print(f"XP: {data.get('xp', 0)}")
        print(f"Unspent Skill Points: {data.get('unspent_points', 0)}")
        print(f"Highest Wave: {data.get('highest_wave', 0)}")
        print(f"Challenge Coins: {data.get('challenge_coins', 0)}")
        print(f"\nBase Stats:")
        print(f"  ATK: {data.get('base_atk', 0)}")
        print(f"  DEF: {data.get('base_defense', 0)}")
        print(f"  Crit Chance: {data.get('base_critchance', 0)}")
        print(f"  Crit Damage: {data.get('base_critdamage', 0)}")
        print(f"  Agility: {data.get('base_agility', 0)}")
        print(f"\nInventory Items: {len(data.get('inventory', []))}")
        print(f"Equipment Slots Filled: {sum(1 for v in data.get('equipment', {}).values() if v)}")
        print("="*60)
    
    def modify_save(self, data):
        """Interactive save modification"""
        while True:
            print("\n" + "="*60)
            print("MODIFY SAVE")
            print("="*60)
            print("1. Modify Gold")
            print("2. Modify Level (also adds 3 skill points per level)")
            print("3. Modify HP")
            print("4. Modify Unspent Skill Points")
            print("5. Modify Challenge Coins")
            print("6. Modify Highest Wave")
            print("7. View Full JSON")
            print("8. Back to Main Menu")
            print("="*60)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                try:
                    new_gold = int(input(f"Current Gold: {data.get('gold', 0)}\nEnter new gold: "))
                    data['gold'] = max(0, new_gold)
                    print(f"✅ Gold set to {data['gold']}")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '2':
                try:
                    current_level = data.get('level', 1)
                    new_level = int(input(f"Current Level: {current_level}\nEnter new level: "))
                    new_level = max(1, new_level)
                    
                    # Calculate skill points to add (3 per level gained)
                    if new_level > current_level:
                        levels_gained = new_level - current_level
                        skill_points_to_add = levels_gained * 3
                        current_points = data.get('unspent_points', 0)
                        data['unspent_points'] = current_points + skill_points_to_add
                        print(f"✅ Level set to {new_level}")
                        print(f"✅ Added {skill_points_to_add} skill points (total: {data['unspent_points']})")
                    else:
                        print(f"✅ Level set to {new_level}")
                    
                    data['level'] = new_level
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '3':
                try:
                    new_hp = int(input(f"Current HP: {data.get('hp', 100)}\nEnter new HP: "))
                    data['hp'] = max(1, new_hp)
                    print(f"✅ HP set to {data['hp']}")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '4':
                try:
                    new_points = int(input(f"Current Unspent Points: {data.get('unspent_points', 0)}\nEnter new points: "))
                    data['unspent_points'] = max(0, new_points)
                    print(f"✅ Unspent Skill Points set to {data['unspent_points']}")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '5':
                try:
                    new_coins = int(input(f"Current Challenge Coins: {data.get('challenge_coins', 0)}\nEnter new coins: "))
                    data['challenge_coins'] = max(0, new_coins)
                    print(f"✅ Challenge Coins set to {data['challenge_coins']}")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '6':
                try:
                    new_wave = int(input(f"Current Highest Wave: {data.get('highest_wave', 0)}\nEnter new wave: "))
                    data['highest_wave'] = max(0, new_wave)
                    print(f"✅ Highest Wave set to {data['highest_wave']}")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == '7':
                print("\n" + json.dumps(data, indent=2))
                input("\nPress Enter to continue...")
            
            elif choice == '8':
                return data
    
    def save_changes(self, data):
        """Save modified data back to file"""
        encoded = self.encode_save(data)
        with open(self.save_file, 'wb') as f:
            f.write(encoded)
        print("✅ Changes saved successfully")
    
    def clear_save(self):
        """Delete save file"""
        if not self.save_file.exists():
            print("❌ No save file to clear")
            return
        
        confirm = input("⚠️  Are you sure you want to delete the save file? (yes/no): ").strip().lower()
        if confirm == 'yes':
            self.save_file.unlink()
            print("✅ Save file deleted")
        else:
            print("❌ Cancelled")
    
    def run(self):
        """Main menu loop"""
        while True:
            print("\n" + "="*60)
            print("VINTAGE LEGENDS - SAVE MANAGER")
            print("="*60)
            print("1. View Save")
            print("2. Modify Save")
            print("3. Clear Save")
            print("4. Exit")
            print("="*60)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                data = self.load_save()
                if data:
                    self.display_save(data)
                    input("\nPress Enter to continue...")
            
            elif choice == '2':
                data = self.load_save()
                if data:
                    self.display_save(data)
                    modified_data = self.modify_save(data)
                    save_confirm = input("\n💾 Save changes? (yes/no): ").strip().lower()
                    if save_confirm == 'yes':
                        self.save_changes(modified_data)
            
            elif choice == '3':
                self.clear_save()
            
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid option")

if __name__ == "__main__":
    tool = SaveManagerTool()
    tool.run()
