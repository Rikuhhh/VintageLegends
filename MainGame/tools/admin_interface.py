"""
Admin Interface for VintageLegends
Easy creation and editing of items and monsters
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path

class AdminInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("VintageLegends - Admin Interface")
        self.root.geometry("900x700")
        
        # Paths
        self.base_path = Path(__file__).resolve().parents[1]
        self.data_path = self.base_path / "data"
        
        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.items_frame = ttk.Frame(self.notebook)
        self.monsters_frame = ttk.Frame(self.notebook)
        self.zones_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.items_frame, text='Items')
        self.notebook.add(self.monsters_frame, text='Monsters')
        self.notebook.add(self.zones_frame, text='Zones')
        
        # Setup tabs
        self.setup_items_tab()
        self.setup_monsters_tab()
        self.setup_zones_tab()
    
    def get_monster_categories(self):
        """Get unique monster categories from monsters.json"""
        try:
            with open(self.data_path / 'monsters.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                categories = set()
                for monster in data.get('enemies', []):
                    if 'category' in monster:
                        categories.add(monster['category'])
                return sorted(list(categories))
        except Exception as e:
            # Fallback to defaults if file can't be read
            return ['beast', 'construct', 'demon', 'dragon', 'undead']
    
    def get_zones(self):
        """Get zones from zones.json"""
        try:
            with open(self.data_path / 'zones.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('zones', [])
        except Exception as e:
            return []
        
    def setup_items_tab(self):
        """Setup the Items tab with form fields"""
        # Left side - Item list
        left_frame = ttk.Frame(self.items_frame)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Existing Items:", font=('Arial', 10, 'bold')).pack()
        
        self.items_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.items_listbox.pack(fill='both', expand=True)
        self.items_listbox.bind('<<ListboxSelect>>', self.load_selected_item)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Item", command=self.new_item).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_item).pack(side='left', padx=2)
        
        # Right side - Item editor
        right_frame = ttk.Frame(self.items_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Item fields
        self.item_fields = {}
        row = 0
        
        # ID
        ttk.Label(scrollable_frame, text="ID*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.item_fields['id'] = ttk.Entry(scrollable_frame, width=40)
        self.item_fields['id'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Name
        ttk.Label(scrollable_frame, text="Name*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.item_fields['name'] = ttk.Entry(scrollable_frame, width=40)
        self.item_fields['name'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Description
        ttk.Label(scrollable_frame, text="Description:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.item_fields['description'] = ttk.Entry(scrollable_frame, width=40)
        self.item_fields['description'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Type
        ttk.Label(scrollable_frame, text="Type*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.item_fields['type'] = ttk.Combobox(scrollable_frame, width=37, 
                                                values=['weapon', 'armor', 'offhand', 'relic', 'consumable', 'material'])
        self.item_fields['type'].grid(row=row, column=1, pady=5)
        self.item_fields['type'].bind('<<ComboboxSelected>>', self.on_type_change)
        row += 1
        
        # Weapon stats (shown conditionally)
        self.weapon_frame = ttk.LabelFrame(scrollable_frame, text="Weapon Stats")
        self.weapon_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(self.weapon_frame, text="Attack:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['attack'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['attack'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(self.weapon_frame, text="Penetration:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['penetration_weapon'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['penetration_weapon'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(self.weapon_frame, text="Crit Chance:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['critchance'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['critchance'].grid(row=2, column=1, padx=5, pady=3)
        
        ttk.Label(self.weapon_frame, text="Crit Damage:").grid(row=3, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['critdamage'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['critdamage'].grid(row=3, column=1, padx=5, pady=3)
        
        # Armor stats (shown conditionally)
        self.armor_frame = ttk.LabelFrame(scrollable_frame, text="Armor Stats")
        self.armor_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(self.armor_frame, text="Defense:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['defense'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['defense'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(self.armor_frame, text="Penetration:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['penetration_armor'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['penetration_armor'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(self.armor_frame, text="Max HP Bonus:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['max_hp'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['max_hp'].grid(row=2, column=1, padx=5, pady=3)
        
        # Consumable stats (shown conditionally)
        self.consumable_frame = ttk.LabelFrame(scrollable_frame, text="Consumable Effects")
        self.consumable_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(self.consumable_frame, text="Heal Amount:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['heal'] = ttk.Entry(self.consumable_frame, width=15)
        self.item_fields['heal'].grid(row=0, column=1, padx=5, pady=3)
        
        # Shop settings
        shop_frame = ttk.LabelFrame(scrollable_frame, text="Shop Settings")
        shop_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        self.item_fields['in_shop'] = tk.BooleanVar()
        ttk.Checkbutton(shop_frame, text="Available in Shop", 
                       variable=self.item_fields['in_shop']).grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=3)
        
        ttk.Label(shop_frame, text="Cost:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['cost'] = ttk.Entry(shop_frame, width=15)
        self.item_fields['cost'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(shop_frame, text="Shop Chance (0-1):").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['shopchance'] = ttk.Entry(shop_frame, width=15)
        self.item_fields['shopchance'].grid(row=2, column=1, padx=5, pady=3)
        
        ttk.Label(shop_frame, text="Gold Variation Min:").grid(row=3, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['goldvar_min'] = ttk.Entry(shop_frame, width=15)
        self.item_fields['goldvar_min'].grid(row=3, column=1, padx=5, pady=3)
        
        ttk.Label(shop_frame, text="Gold Variation Max:").grid(row=4, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['goldvar_max'] = ttk.Entry(shop_frame, width=15)
        self.item_fields['goldvar_max'].grid(row=4, column=1, padx=5, pady=3)
        
        ttk.Label(shop_frame, text="Shop Zones:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(shop_frame, text="(Leave all unchecked for all zones)", font=('Arial', 8)).grid(row=5, column=1, sticky='w', padx=5)
        
        # Shop zones checkboxes
        self.item_fields['shop_zones'] = {}
        zones = self.get_zones()
        zone_row = 6
        for i, zone in enumerate(zones):
            zone_id = zone.get('id')
            zone_name = zone.get('name', zone_id)
            self.item_fields['shop_zones'][zone_id] = tk.BooleanVar()
            ttk.Checkbutton(shop_frame, text=zone_name, 
                          variable=self.item_fields['shop_zones'][zone_id]).grid(
                              row=zone_row + (i // 2), column=i % 2, sticky='w', padx=10, pady=3)
        
        # Drop settings
        drop_frame = ttk.LabelFrame(scrollable_frame, text="Drop Settings")
        drop_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        self.item_fields['droppable'] = tk.BooleanVar()
        ttk.Checkbutton(drop_frame, text="Droppable", 
                       variable=self.item_fields['droppable']).grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=3)
        
        ttk.Label(drop_frame, text="Dropped By:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['dropped_by'] = ttk.Combobox(drop_frame, width=12,
                                                      values=self.get_monster_categories())
        self.item_fields['dropped_by'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(drop_frame, text="Drop Chance (0-1):").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['drop_chance'] = ttk.Entry(drop_frame, width=15)
        self.item_fields['drop_chance'].grid(row=2, column=1, padx=5, pady=3)
        
        # Image settings
        image_frame = ttk.LabelFrame(scrollable_frame, text="Image Settings")
        image_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(image_frame, text="Image Filename:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['image'] = ttk.Entry(image_frame, width=30)
        self.item_fields['image'].grid(row=0, column=1, padx=5, pady=3)
        ttk.Label(image_frame, text="(e.g. potion.png - in assets/images/items/)", 
                 font=('Arial', 8)).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=3)
        
        # Save button
        ttk.Button(scrollable_frame, text="Save Item", command=self.save_item, 
                  style='Accent.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load items
        self.load_items_list()
        
    def setup_monsters_tab(self):
        """Setup the Monsters tab with form fields"""
        # Left side - Monster list
        left_frame = ttk.Frame(self.monsters_frame)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Existing Monsters:", font=('Arial', 10, 'bold')).pack()
        
        self.monsters_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.monsters_listbox.pack(fill='both', expand=True)
        self.monsters_listbox.bind('<<ListboxSelect>>', self.load_selected_monster)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Monster", command=self.new_monster).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_monster).pack(side='left', padx=2)
        
        # Right side - Monster editor
        right_frame = ttk.Frame(self.monsters_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Monster fields
        self.monster_fields = {}
        row = 0
        
        # ID
        ttk.Label(scrollable_frame, text="ID*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.monster_fields['id'] = ttk.Entry(scrollable_frame, width=40)
        self.monster_fields['id'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Name
        ttk.Label(scrollable_frame, text="Name*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.monster_fields['name'] = ttk.Entry(scrollable_frame, width=40)
        self.monster_fields['name'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Classification
        ttk.Label(scrollable_frame, text="Classification*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.monster_fields['classification'] = ttk.Combobox(scrollable_frame, width=37,
                                                            values=['normal', 'elite', 'miniboss', 'boss'])
        self.monster_fields['classification'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Category
        ttk.Label(scrollable_frame, text="Category*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.monster_fields['category'] = ttk.Combobox(scrollable_frame, width=37,
                                                       values=self.get_monster_categories())
        self.monster_fields['category'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Base stats frame
        stats_frame = ttk.LabelFrame(scrollable_frame, text="Base Stats")
        stats_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(stats_frame, text="HP Base:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['hp_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['hp_base'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="ATK Base:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['atk_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['atk_base'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="DEF Base:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['def_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['def_base'].grid(row=2, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Penetration Base:").grid(row=3, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['pen_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['pen_base'].grid(row=3, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="XP Base:").grid(row=0, column=2, sticky='w', padx=5, pady=3)
        self.monster_fields['xp_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['xp_base'].grid(row=0, column=3, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Gold Base:").grid(row=1, column=2, sticky='w', padx=5, pady=3)
        self.monster_fields['gold_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['gold_base'].grid(row=1, column=3, padx=5, pady=3)
        
        # Spawn settings
        spawn_frame = ttk.LabelFrame(scrollable_frame, text="Spawn Settings")
        spawn_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(spawn_frame, text="Min Wave (0=any):").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['min_wave'] = ttk.Entry(spawn_frame, width=15)
        self.monster_fields['min_wave'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(spawn_frame, text="Max Wave (0=any):").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['max_wave'] = ttk.Entry(spawn_frame, width=15)
        self.monster_fields['max_wave'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(spawn_frame, text="Spawn on Wave Multiple:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['spawn_multiple'] = ttk.Entry(spawn_frame, width=15)
        self.monster_fields['spawn_multiple'].grid(row=2, column=1, padx=5, pady=3)
        
        # Image settings
        image_frame = ttk.LabelFrame(scrollable_frame, text="Image Settings")
        image_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(image_frame, text="Image Filename:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.monster_fields['image'] = ttk.Entry(image_frame, width=30)
        self.monster_fields['image'].grid(row=0, column=1, padx=5, pady=3)
        ttk.Label(image_frame, text="(e.g. wolf.png - in assets/images/monsters/)", 
                 font=('Arial', 8)).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=3)
        
        # Save button
        ttk.Button(scrollable_frame, text="Save Monster", command=self.save_monster,
                  style='Accent.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load monsters
        self.load_monsters_list()
    
    def on_type_change(self, event=None):
        """Show/hide relevant stat frames based on item type"""
        item_type = self.item_fields['type'].get()
        
        if item_type == 'weapon':
            self.weapon_frame.grid()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid_remove()
        elif item_type in ['armor', 'offhand', 'relic']:
            # All equipment types can use weapon and armor frames for stats
            self.weapon_frame.grid()  # Relics/offhand can have attack too
            self.armor_frame.grid()   # Can have defense too
            self.consumable_frame.grid_remove()
        elif item_type == 'consumable':
            self.weapon_frame.grid_remove()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid()
        else:
            self.weapon_frame.grid_remove()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid_remove()
    
    def load_items_list(self):
        """Load items from items.json into the listbox"""
        self.items_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'items.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items_data = data.get('items', [])
                for item in self.items_data:
                    self.items_listbox.insert(tk.END, f"{item.get('id')} - {item.get('name')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load items: {e}")
            self.items_data = []
    
    def load_monsters_list(self):
        """Load monsters from monsters.json into the listbox"""
        self.monsters_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'monsters.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.monsters_data = data.get('enemies', [])
                for monster in self.monsters_data:
                    self.monsters_listbox.insert(tk.END, f"{monster.get('id')} - {monster.get('name')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load monsters: {e}")
            self.monsters_data = []
    
    def load_selected_item(self, event):
        """Load selected item into the form"""
        selection = self.items_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        item = self.items_data[idx]
        
        # Clear all fields first
        self.clear_item_form()
        
        # Load basic fields
        self.item_fields['id'].insert(0, item.get('id', ''))
        self.item_fields['name'].insert(0, item.get('name', ''))
        self.item_fields['description'].insert(0, item.get('description', ''))
        self.item_fields['type'].set(item.get('type', 'material'))
        
        # Weapon stats
        if item.get('attack'):
            self.item_fields['attack'].insert(0, str(item.get('attack')))
        if item.get('penetration'):
            self.item_fields['penetration_weapon'].insert(0, str(item.get('penetration')))
        if item.get('critchance'):
            self.item_fields['critchance'].insert(0, str(item.get('critchance')))
        if item.get('critdamage'):
            self.item_fields['critdamage'].insert(0, str(item.get('critdamage')))
        
        # Armor stats
        if item.get('defense'):
            self.item_fields['defense'].insert(0, str(item.get('defense')))
            if item.get('penetration') and not self.item_fields['penetration_weapon'].get():
                self.item_fields['penetration_armor'].insert(0, str(item.get('penetration', '')))
        if item.get('max_hp'):
            self.item_fields['max_hp'].insert(0, str(item.get('max_hp')))
        
        # Consumable stats
        if item.get('effect', {}).get('heal'):
            self.item_fields['heal'].insert(0, str(item['effect']['heal']))
        
        # Shop settings
        if item.get('cost'):
            self.item_fields['in_shop'].set(True)
            self.item_fields['cost'].insert(0, str(item.get('cost')))
        if item.get('shopchance'):
            self.item_fields['shopchance'].insert(0, str(item.get('shopchance')))
        
        goldvar = item.get('goldvariation', [])
        if isinstance(goldvar, list) and len(goldvar) >= 2:
            self.item_fields['goldvar_min'].insert(0, str(goldvar[0]))
            self.item_fields['goldvar_max'].insert(0, str(goldvar[1]))
        
        # Drop settings
        if item.get('droppable'):
            self.item_fields['droppable'].set(True)
        if item.get('dropped_by'):
            self.item_fields['dropped_by'].set(item.get('dropped_by'))
        if item.get('drop_chance'):
            self.item_fields['drop_chance'].insert(0, str(item.get('drop_chance')))
        
        # Image settings
        if item.get('image'):
            self.item_fields['image'].insert(0, item.get('image'))
        
        # Shop zones
        shop_zones = item.get('shop_zones', [])
        for zone_id, var in self.item_fields['shop_zones'].items():
            var.set(zone_id in shop_zones)
        
        # Update UI
        self.on_type_change()
    
    def load_selected_monster(self, event):
        """Load selected monster into the form"""
        selection = self.monsters_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        monster = self.monsters_data[idx]
        
        # Clear all fields first
        self.clear_monster_form()
        
        # Load fields
        self.monster_fields['id'].insert(0, monster.get('id', ''))
        self.monster_fields['name'].insert(0, monster.get('name', ''))
        self.monster_fields['classification'].set(monster.get('classification', 'normal'))
        self.monster_fields['category'].set(monster.get('category', 'beast'))
        
        self.monster_fields['hp_base'].insert(0, str(monster.get('hp_base', '')))
        self.monster_fields['atk_base'].insert(0, str(monster.get('atk_base', '')))
        self.monster_fields['def_base'].insert(0, str(monster.get('def_base', '')))
        self.monster_fields['pen_base'].insert(0, str(monster.get('pen_base', '')))
        self.monster_fields['xp_base'].insert(0, str(monster.get('xp_base', '')))
        self.monster_fields['gold_base'].insert(0, str(monster.get('gold_base', '')))
        
        self.monster_fields['min_wave'].insert(0, str(monster.get('min_wave', '')))
        self.monster_fields['max_wave'].insert(0, str(monster.get('max_wave', '')))
        self.monster_fields['spawn_multiple'].insert(0, str(monster.get('spawn_on_wave_multiple_of', '')))
        self.monster_fields['image'].insert(0, str(monster.get('image', '')))
    
    def clear_item_form(self):
        """Clear all item form fields"""
        for key, field in self.item_fields.items():
            if key == 'shop_zones':
                for var in field.values():
                    var.set(False)
            elif isinstance(field, tk.BooleanVar):
                field.set(False)
            elif isinstance(field, (ttk.Entry, ttk.Combobox)):
                field.delete(0, tk.END)
    
    def clear_monster_form(self):
        """Clear all monster form fields"""
        for key, field in self.monster_fields.items():
            if isinstance(field, (ttk.Entry, ttk.Combobox)):
                field.delete(0, tk.END)
    
    def new_item(self):
        """Clear form for new item creation"""
        self.clear_item_form()
        self.items_listbox.selection_clear(0, tk.END)
    
    def new_monster(self):
        """Clear form for new monster creation"""
        self.clear_monster_form()
        self.monsters_listbox.selection_clear(0, tk.END)
    
    def save_item(self):
        """Save item to items.json"""
        # Validate required fields
        if not self.item_fields['id'].get() or not self.item_fields['name'].get() or not self.item_fields['type'].get():
            messagebox.showerror("Error", "ID, Name, and Type are required!")
            return
        
        # Build item dict
        item = {
            'id': self.item_fields['id'].get(),
            'name': self.item_fields['name'].get(),
            'type': self.item_fields['type'].get(),
        }
        
        if self.item_fields['description'].get():
            item['description'] = self.item_fields['description'].get()
        
        # Type-specific stats
        itype = self.item_fields['type'].get()
        
        # Weapon stats
        if itype in ['weapon', 'offhand', 'relic']:
            if self.item_fields['attack'].get():
                item['attack'] = int(self.item_fields['attack'].get())
            if self.item_fields['penetration_weapon'].get():
                item['penetration'] = float(self.item_fields['penetration_weapon'].get())
            if self.item_fields['critchance'].get():
                item['critchance'] = float(self.item_fields['critchance'].get())
            if self.item_fields['critdamage'].get():
                item['critdamage'] = float(self.item_fields['critdamage'].get())
        
        # Armor/defensive stats
        if itype in ['armor', 'offhand', 'relic']:
            if self.item_fields['defense'].get():
                item['defense'] = int(self.item_fields['defense'].get())
            if self.item_fields['penetration_armor'].get() and not item.get('penetration'):
                item['penetration'] = float(self.item_fields['penetration_armor'].get())
            if self.item_fields['max_hp'].get():
                item['max_hp'] = int(self.item_fields['max_hp'].get())
        
        # Consumable stats
        if itype == 'consumable':
            if self.item_fields['heal'].get():
                item['effect'] = {'heal': int(self.item_fields['heal'].get())}
        
        # Shop settings
        if self.item_fields['in_shop'].get() and self.item_fields['cost'].get():
            item['cost'] = int(self.item_fields['cost'].get())
            if self.item_fields['shopchance'].get():
                item['shopchance'] = float(self.item_fields['shopchance'].get())
            
            if self.item_fields['goldvar_min'].get() and self.item_fields['goldvar_max'].get():
                item['goldvariation'] = [
                    float(self.item_fields['goldvar_min'].get()),
                    float(self.item_fields['goldvar_max'].get())
                ]
            
            # Shop zones
            shop_zones = [zone_id for zone_id, var in self.item_fields['shop_zones'].items() if var.get()]
            if shop_zones:
                item['shop_zones'] = shop_zones
        
        # Drop settings
        if self.item_fields['droppable'].get():
            item['droppable'] = True
            if self.item_fields['dropped_by'].get():
                item['dropped_by'] = self.item_fields['dropped_by'].get()
            if self.item_fields['drop_chance'].get():
                item['drop_chance'] = float(self.item_fields['drop_chance'].get())
        
        # Image settings
        if self.item_fields['image'].get():
            item['image'] = self.item_fields['image'].get()
        
        # Find if updating or creating new
        item_id = item['id']
        found = False
        for i, existing in enumerate(self.items_data):
            if existing.get('id') == item_id:
                self.items_data[i] = item
                found = True
                break
        
        if not found:
            self.items_data.append(item)
        
        # Save to file
        try:
            with open(self.data_path / 'items.json', 'w', encoding='utf-8') as f:
                json.dump({'items': self.items_data}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Item '{item['name']}' saved successfully!")
            self.load_items_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save item: {e}")
    
    def save_monster(self):
        """Save monster to monsters.json"""
        # Validate required fields
        if not self.monster_fields['id'].get() or not self.monster_fields['name'].get():
            messagebox.showerror("Error", "ID and Name are required!")
            return
        
        # Build monster dict
        monster = {
            'id': self.monster_fields['id'].get(),
            'name': self.monster_fields['name'].get(),
            'classification': self.monster_fields['classification'].get() or 'normal',
            'category': self.monster_fields['category'].get() or 'beast',
        }
        
        # Stats
        if self.monster_fields['hp_base'].get():
            monster['hp_base'] = int(self.monster_fields['hp_base'].get())
        if self.monster_fields['atk_base'].get():
            monster['atk_base'] = int(self.monster_fields['atk_base'].get())
        if self.monster_fields['def_base'].get():
            monster['def_base'] = int(self.monster_fields['def_base'].get())
        if self.monster_fields['pen_base'].get():
            monster['pen_base'] = float(self.monster_fields['pen_base'].get())
        if self.monster_fields['xp_base'].get():
            monster['xp_base'] = int(self.monster_fields['xp_base'].get())
        if self.monster_fields['gold_base'].get():
            monster['gold_base'] = int(self.monster_fields['gold_base'].get())
        
        # Spawn settings
        if self.monster_fields['min_wave'].get():
            monster['min_wave'] = int(self.monster_fields['min_wave'].get())
        if self.monster_fields['max_wave'].get():
            monster['max_wave'] = int(self.monster_fields['max_wave'].get())
        if self.monster_fields['spawn_multiple'].get():
            monster['spawn_on_wave_multiple_of'] = int(self.monster_fields['spawn_multiple'].get())
        
        # Image settings
        if self.monster_fields['image'].get():
            monster['image'] = self.monster_fields['image'].get()
        
        # Placeholder for attacks and drops (can be extended)
        if 'attacks' not in monster:
            monster['attacks'] = []
        if 'drops' not in monster:
            monster['drops'] = []
        
        # Find if updating or creating new
        monster_id = monster['id']
        found = False
        for i, existing in enumerate(self.monsters_data):
            if existing.get('id') == monster_id:
                # Preserve attacks and drops if they exist
                if 'attacks' in existing:
                    monster['attacks'] = existing['attacks']
                if 'drops' in existing:
                    monster['drops'] = existing['drops']
                self.monsters_data[i] = monster
                found = True
                break
        
        if not found:
            self.monsters_data.append(monster)
        
        # Save to file - preserve scaling_notes
        try:
            with open(self.data_path / 'monsters.json', 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            full_data['enemies'] = self.monsters_data
            
            with open(self.data_path / 'monsters.json', 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Monster '{monster['name']}' saved successfully!")
            self.load_monsters_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save monster: {e}")
    
    def delete_item(self):
        """Delete selected item"""
        selection = self.items_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        idx = selection[0]
        item = self.items_data[idx]
        
        if messagebox.askyesno("Confirm Delete", f"Delete item '{item.get('name')}'?"):
            self.items_data.pop(idx)
            try:
                with open(self.data_path / 'items.json', 'w', encoding='utf-8') as f:
                    json.dump({'items': self.items_data}, f, indent=2, ensure_ascii=False)
                self.load_items_list()
                self.clear_item_form()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item: {e}")
    
    def delete_monster(self):
        """Delete selected monster"""
        selection = self.monsters_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a monster to delete")
            return
        
        idx = selection[0]
        monster = self.monsters_data[idx]
        
        if messagebox.askyesno("Confirm Delete", f"Delete monster '{monster.get('name')}'?"):
            self.monsters_data.pop(idx)
            try:
                with open(self.data_path / 'monsters.json', 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
                
                full_data['enemies'] = self.monsters_data
                
                with open(self.data_path / 'monsters.json', 'w', encoding='utf-8') as f:
                    json.dump(full_data, f, indent=2, ensure_ascii=False)
                self.load_monsters_list()
                self.clear_monster_form()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete monster: {e}")
    
    def setup_zones_tab(self):
        """Setup the Zones tab with form fields"""
        # Left side - Zone list
        left_frame = ttk.Frame(self.zones_frame)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Existing Zones:", font=('Arial', 10, 'bold')).pack()
        
        self.zones_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.zones_listbox.pack(fill='both', expand=True)
        self.zones_listbox.bind('<<ListboxSelect>>', self.load_selected_zone)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Zone", command=self.new_zone).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_zone).pack(side='left', padx=2)
        
        # Right side - Zone editor
        right_frame = ttk.Frame(self.zones_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(right_frame)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Zone fields
        self.zone_fields = {}
        row = 0
        
        # ID
        ttk.Label(scrollable_frame, text="ID*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.zone_fields['id'] = ttk.Entry(scrollable_frame, width=40)
        self.zone_fields['id'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Name
        ttk.Label(scrollable_frame, text="Name*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.zone_fields['name'] = ttk.Entry(scrollable_frame, width=40)
        self.zone_fields['name'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Spawn Settings
        spawn_frame = ttk.LabelFrame(scrollable_frame, text="Spawn Settings")
        spawn_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(spawn_frame, text="Spawn Chance (% per 10 waves)*:", font=('Arial', 9)).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.zone_fields['spawn_chance'] = ttk.Entry(spawn_frame, width=15)
        self.zone_fields['spawn_chance'].grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(spawn_frame, text="(0-100)", font=('Arial', 8)).grid(row=0, column=2, sticky='w', padx=5)
        
        ttk.Label(spawn_frame, text="Minimum Wave*:", font=('Arial', 9)).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.zone_fields['min_wave'] = ttk.Entry(spawn_frame, width=15)
        self.zone_fields['min_wave'].grid(row=1, column=1, padx=5, pady=5)
        
        # Background Image
        bg_frame = ttk.LabelFrame(scrollable_frame, text="Background Image")
        bg_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(bg_frame, text="Image Filename:", font=('Arial', 9)).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.zone_fields['background_image'] = ttk.Entry(bg_frame, width=30)
        self.zone_fields['background_image'].grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(bg_frame, text="(e.g. flowerfield.png - in assets/images/backgrounds/)", 
                 font=('Arial', 8)).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=3)
        
        # Enemy Types
        enemy_frame = ttk.LabelFrame(scrollable_frame, text="Enemy Types Allowed")
        enemy_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        enemy_types = self.get_monster_categories()
        self.zone_fields['enemy_types'] = {}
        
        for i, enemy_type in enumerate(enemy_types):
            self.zone_fields['enemy_types'][enemy_type] = tk.BooleanVar()
            ttk.Checkbutton(enemy_frame, text=enemy_type.capitalize(), 
                          variable=self.zone_fields['enemy_types'][enemy_type]).grid(
                              row=i // 2, column=i % 2, sticky='w', padx=10, pady=5)
        
        # Save button
        ttk.Button(scrollable_frame, text="Save Zone", command=self.save_zone,
                  style='Accent.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load zones
        self.load_zones_list()
    
    def load_zones_list(self):
        """Load zones from zones.json into the listbox"""
        self.zones_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'zones.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.zones_data = data.get('zones', [])
                for zone in self.zones_data:
                    self.zones_listbox.insert(tk.END, f"{zone.get('id')} - {zone.get('name')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load zones: {e}")
            self.zones_data = []
    
    def load_selected_zone(self, event):
        """Load selected zone into the form"""
        selection = self.zones_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        zone = self.zones_data[idx]
        
        # Clear all fields first
        self.clear_zone_form()
        
        # Load fields
        self.zone_fields['id'].insert(0, zone.get('id', ''))
        self.zone_fields['name'].insert(0, zone.get('name', ''))
        self.zone_fields['spawn_chance'].insert(0, str(zone.get('spawn_chance', '')))
        self.zone_fields['min_wave'].insert(0, str(zone.get('min_wave', '')))
        self.zone_fields['background_image'].insert(0, zone.get('background_image', ''))
        
        # Load enemy types
        enemy_types = zone.get('enemy_types', {})
        for enemy_type, var in self.zone_fields['enemy_types'].items():
            var.set(enemy_types.get(enemy_type, False))
    
    def clear_zone_form(self):
        """Clear all zone form fields"""
        for key, field in self.zone_fields.items():
            if key == 'enemy_types':
                for var in field.values():
                    var.set(False)
            elif isinstance(field, (ttk.Entry, ttk.Combobox)):
                field.delete(0, tk.END)
    
    def new_zone(self):
        """Clear form for new zone creation"""
        self.clear_zone_form()
        self.zones_listbox.selection_clear(0, tk.END)
    
    def save_zone(self):
        """Save zone to zones.json"""
        # Validate required fields
        if not self.zone_fields['id'].get() or not self.zone_fields['name'].get():
            messagebox.showerror("Error", "ID and Name are required!")
            return
        
        if not self.zone_fields['spawn_chance'].get() or not self.zone_fields['min_wave'].get():
            messagebox.showerror("Error", "Spawn Chance and Minimum Wave are required!")
            return
        
        try:
            spawn_chance = float(self.zone_fields['spawn_chance'].get())
            if spawn_chance < 0 or spawn_chance > 100:
                messagebox.showerror("Error", "Spawn Chance must be between 0 and 100!")
                return
        except ValueError:
            messagebox.showerror("Error", "Spawn Chance must be a number!")
            return
        
        try:
            min_wave = int(self.zone_fields['min_wave'].get())
            if min_wave < 1:
                messagebox.showerror("Error", "Minimum Wave must be at least 1!")
                return
        except ValueError:
            messagebox.showerror("Error", "Minimum Wave must be a number!")
            return
        
        # Build zone dict
        zone = {
            'id': self.zone_fields['id'].get(),
            'name': self.zone_fields['name'].get(),
            'spawn_chance': spawn_chance,
            'min_wave': min_wave,
            'background_image': self.zone_fields['background_image'].get(),
            'enemy_types': {}
        }
        
        # Get enemy types (ensure all current categories are included)
        for enemy_type in self.get_monster_categories():
            if enemy_type in self.zone_fields['enemy_types']:
                zone['enemy_types'][enemy_type] = self.zone_fields['enemy_types'][enemy_type].get()
            else:
                zone['enemy_types'][enemy_type] = False
        
        # Find if updating or creating new
        zone_id = zone['id']
        found = False
        for i, existing in enumerate(self.zones_data):
            if existing.get('id') == zone_id:
                self.zones_data[i] = zone
                found = True
                break
        
        if not found:
            self.zones_data.append(zone)
        
        # Save to file
        try:
            with open(self.data_path / 'zones.json', 'w', encoding='utf-8') as f:
                json.dump({'zones': self.zones_data}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Zone '{zone['name']}' saved successfully!")
            self.load_zones_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save zone: {e}")
    
    def delete_zone(self):
        """Delete selected zone"""
        selection = self.zones_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a zone to delete")
            return
        
        idx = selection[0]
        zone = self.zones_data[idx]
        
        if messagebox.askyesno("Confirm Delete", f"Delete zone '{zone.get('name')}'?"):
            self.zones_data.pop(idx)
            try:
                with open(self.data_path / 'zones.json', 'w', encoding='utf-8') as f:
                    json.dump({'zones': self.zones_data}, f, indent=2, ensure_ascii=False)
                self.load_zones_list()
                self.clear_zone_form()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete zone: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AdminInterface(root)
    root.mainloop()
