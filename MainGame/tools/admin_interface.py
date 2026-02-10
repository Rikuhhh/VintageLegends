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
        self.root.title("VintageLegends - Admin Interface v2.0")
        self.root.geometry("1100x750")
        
        # Style configuration
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#2E86AB')
        style.configure('Section.TLabelframe.Label', font=('Arial', 10, 'bold'))
        style.configure('Save.TButton', font=('Arial', 10, 'bold'), foreground='green')
        
        # Add header
        header_frame = ttk.Frame(root, relief='raised', borderwidth=2)
        header_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(header_frame, text="VintageLegends Admin Interface", 
                 font=('Arial', 14, 'bold')).pack(pady=5)
        ttk.Label(header_frame, text="Complete Game Data Editor - Items, Monsters, Skills, Zones & Recipes", 
                 font=('Arial', 9, 'italic')).pack(pady=(0, 5))
        
        # Paths
        self.base_path = Path(__file__).resolve().parents[1]
        self.data_path = self.base_path / "data"
        
        # Status bar at bottom
        status_frame = ttk.Frame(root, relief='sunken', borderwidth=1)
        status_frame.pack(fill='x', side='bottom', padx=5, pady=5)
        ttk.Label(status_frame, text=f"Data Path: {self.data_path}", 
                 font=('Arial', 8)).pack(side='left', padx=10, pady=2)
        
        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.items_frame = ttk.Frame(self.notebook)
        self.monsters_frame = ttk.Frame(self.notebook)
        self.skills_frame = ttk.Frame(self.notebook)
        self.zones_frame = ttk.Frame(self.notebook)
        self.recipes_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.items_frame, text='Items')
        self.notebook.add(self.monsters_frame, text='Monsters')
        self.notebook.add(self.skills_frame, text='Skills')
        self.notebook.add(self.zones_frame, text='Zones')
        self.notebook.add(self.recipes_frame, text='Recipes')
        
        # Setup tabs
        self.setup_items_tab()
        self.setup_monsters_tab()
        self.setup_skills_tab()
        self.setup_zones_tab()
        self.setup_recipes_tab()
    
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
        
        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill='x', pady=5)
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=2)
        self.item_search_var = tk.StringVar()
        self.item_search_var.trace('w', self.filter_items)
        ttk.Entry(search_frame, textvariable=self.item_search_var, width=20).pack(side='left', padx=2)
        
        self.items_listbox = tk.Listbox(left_frame, width=35, height=25)
        self.items_listbox.pack(fill='both', expand=True)
        self.items_listbox.bind('<<ListboxSelect>>', self.load_selected_item)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Item", command=self.new_item).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_item).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_item).pack(side='left', padx=2)
        
        # Status label
        self.item_count_label = ttk.Label(left_frame, text="Items: 0", font=('Arial', 8, 'italic'))
        self.item_count_label.pack(pady=5)
        
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
                                                values=['weapon', 'armor', 'offhand', 'relic', 'consumable', 'material', 'container'])
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
        
        ttk.Label(self.weapon_frame, text="Magic Power:").grid(row=0, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['magic_power'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['magic_power'].grid(row=0, column=3, padx=5, pady=3)
        
        ttk.Label(self.weapon_frame, text="Magic Penetration:").grid(row=1, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['magic_penetration'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['magic_penetration'].grid(row=1, column=3, padx=5, pady=3)
        
        ttk.Label(self.weapon_frame, text="Lifesteal (%):").grid(row=2, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['lifesteal'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['lifesteal'].grid(row=2, column=3, padx=5, pady=3)
        ttk.Label(self.weapon_frame, text="(% of dmg as HP)", font=('Arial', 7, 'italic')).grid(row=2, column=4, sticky='w', padx=2)
        
        ttk.Label(self.weapon_frame, text="Agility:").grid(row=3, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['agility'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['agility'].grid(row=3, column=3, padx=5, pady=3)
        ttk.Label(self.weapon_frame, text="(boosts crit & dodge)", font=('Arial', 7, 'italic')).grid(row=3, column=4, sticky='w', padx=2)
        
        ttk.Label(self.weapon_frame, text="Exp Gain (%):").grid(row=4, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['exp_gain'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['exp_gain'].grid(row=4, column=1, padx=5, pady=3)
        ttk.Label(self.weapon_frame, text="(% bonus exp)", font=('Arial', 7, 'italic')).grid(row=4, column=2, sticky='w', padx=2)
        
        ttk.Label(self.weapon_frame, text="Gold Gain (%):").grid(row=5, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['gold_gain'] = ttk.Entry(self.weapon_frame, width=15)
        self.item_fields['gold_gain'].grid(row=5, column=1, padx=5, pady=3)
        ttk.Label(self.weapon_frame, text="(% bonus gold)", font=('Arial', 7, 'italic')).grid(row=5, column=2, sticky='w', padx=2)
        
        # Armor stats (shown conditionally)
        self.armor_frame = ttk.LabelFrame(scrollable_frame, text="🛡️ Defensive Stats (Armor/Relics/Offhand)", style='Section.TLabelframe')
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
        
        ttk.Label(self.armor_frame, text="Max Mana Bonus:").grid(row=0, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['max_mana'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['max_mana'].grid(row=0, column=3, padx=5, pady=3)
        
        ttk.Label(self.armor_frame, text="Mana Regen:").grid(row=1, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['mana_regen'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['mana_regen'].grid(row=1, column=3, padx=5, pady=3)
        
        ttk.Label(self.armor_frame, text="HP Regen:").grid(row=2, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['hp_regen'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['hp_regen'].grid(row=2, column=3, padx=5, pady=3)
        ttk.Label(self.armor_frame, text="(HP/turn)", font=('Arial', 7, 'italic')).grid(row=2, column=4, sticky='w', padx=2)
        
        ttk.Label(self.armor_frame, text="Dodge Chance (%):").grid(row=3, column=2, sticky='w', padx=5, pady=3)
        self.item_fields['dodge_chance'] = ttk.Entry(self.armor_frame, width=15)
        self.item_fields['dodge_chance'].grid(row=3, column=3, padx=5, pady=3)
        ttk.Label(self.armor_frame, text="(avoid attacks)", font=('Arial', 7, 'italic')).grid(row=3, column=4, sticky='w', padx=2)
        
        # Consumable stats (shown conditionally)
        self.consumable_frame = ttk.LabelFrame(scrollable_frame, text="🧪 Consumable Effects", style='Section.TLabelframe')
        self.consumable_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(self.consumable_frame, text="Heal Amount:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['heal'] = ttk.Entry(self.consumable_frame, width=15)
        self.item_fields['heal'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(self.consumable_frame, text="Heal % (0-1):").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['heal_percent'] = ttk.Entry(self.consumable_frame, width=15)
        self.item_fields['heal_percent'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(self.consumable_frame, text="Restore Mana:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.item_fields['restore_mana'] = ttk.Entry(self.consumable_frame, width=15)
        self.item_fields['restore_mana'].grid(row=2, column=1, padx=5, pady=3)
        
        # Container settings (shown conditionally)
        self.container_frame = ttk.LabelFrame(scrollable_frame, text="📦 Container Loot Pool", style='Section.TLabelframe')
        self.container_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        # Loot pool editor
        self.loot_pool_entries = []
        loot_info = ttk.Label(self.container_frame, text="Configure loot drops (item_id OR skill_id, chance 0-1, optional qty)", 
                             font=('Arial', 8, 'italic'))
        loot_info.grid(row=0, column=0, columnspan=6, sticky='w', padx=5, pady=5)
        
        # Headers
        ttk.Label(self.container_frame, text="Type", font=('Arial', 8, 'bold')).grid(row=1, column=0, padx=5)
        ttk.Label(self.container_frame, text="ID", font=('Arial', 8, 'bold')).grid(row=1, column=1, padx=5)
        ttk.Label(self.container_frame, text="Chance", font=('Arial', 8, 'bold')).grid(row=1, column=2, padx=5)
        ttk.Label(self.container_frame, text="Qty", font=('Arial', 8, 'bold')).grid(row=1, column=3, padx=5)
        
        # Add 5 loot entry rows
        for i in range(5):
            loot_row = 2 + i
            entry_type = ttk.Combobox(self.container_frame, width=8, values=['item', 'skill'])
            entry_type.grid(row=loot_row, column=0, padx=2, pady=2)
            
            entry_id = ttk.Entry(self.container_frame, width=20)
            entry_id.grid(row=loot_row, column=1, padx=2, pady=2)
            
            entry_chance = ttk.Entry(self.container_frame, width=8)
            entry_chance.grid(row=loot_row, column=2, padx=2, pady=2)
            
            entry_qty = ttk.Entry(self.container_frame, width=6)
            entry_qty.grid(row=loot_row, column=3, padx=2, pady=2)
            
            self.loot_pool_entries.append({
                'type': entry_type,
                'id': entry_id,
                'chance': entry_chance,
                'qty': entry_qty
            })
        
        # Shop settings
        shop_frame = ttk.LabelFrame(scrollable_frame, text="🛒 Shop Settings", style='Section.TLabelframe')
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
        drop_frame = ttk.LabelFrame(scrollable_frame, text="💎 Drop Settings (Monster Loot)", style='Section.TLabelframe')
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
        ttk.Button(scrollable_frame, text="💾 Save Item", command=self.save_item, 
                  style='Save.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load items
        self.load_items_list()
        
    def setup_monsters_tab(self):
        """Setup the Monsters tab with form fields"""
        # Left side - Monster list
        left_frame = ttk.Frame(self.monsters_frame)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Existing Monsters:", font=('Arial', 10, 'bold')).pack()
        
        # Search box
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill='x', pady=5)
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=2)
        self.monster_search_var = tk.StringVar()
        self.monster_search_var.trace('w', self.filter_monsters)
        ttk.Entry(search_frame, textvariable=self.monster_search_var, width=20).pack(side='left', padx=2)
        
        self.monsters_listbox = tk.Listbox(left_frame, width=35, height=25)
        self.monsters_listbox.pack(fill='both', expand=True)
        self.monsters_listbox.bind('<<ListboxSelect>>', self.load_selected_monster)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Monster", command=self.new_monster).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Duplicate", command=self.duplicate_monster).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_monster).pack(side='left', padx=2)
        
        # Status label
        self.monster_count_label = ttk.Label(left_frame, text="Monsters: 0", font=('Arial', 8, 'italic'))
        self.monster_count_label.pack(pady=5)
        
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
        stats_frame = ttk.LabelFrame(scrollable_frame, text="📊 Base Stats", style='Section.TLabelframe')
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
        
        ttk.Label(stats_frame, text="Magic Def Base:").grid(row=2, column=2, sticky='w', padx=5, pady=3)
        self.monster_fields['magic_def_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['magic_def_base'].grid(row=2, column=3, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="XP Base:").grid(row=0, column=2, sticky='w', padx=5, pady=3)
        self.monster_fields['xp_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['xp_base'].grid(row=0, column=3, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Gold Base:").grid(row=1, column=2, sticky='w', padx=5, pady=3)
        self.monster_fields['gold_base'] = ttk.Entry(stats_frame, width=15)
        self.monster_fields['gold_base'].grid(row=1, column=3, padx=5, pady=3)
        
        # Spawn settings
        spawn_frame = ttk.LabelFrame(scrollable_frame, text="🌍 Spawn Settings", style='Section.TLabelframe')
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
        
        # Drop settings
        drops_frame = ttk.LabelFrame(scrollable_frame, text="💎 Item Drops Configuration", style='Section.TLabelframe')
        drops_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        # Drops pool editor
        self.monster_drop_entries = []
        drops_info = ttk.Label(drops_frame, text="Configure item drops (item_id, chance 0-1, qty_min, qty_max)", 
                             font=('Arial', 8, 'italic'))
        drops_info.grid(row=0, column=0, columnspan=6, sticky='w', padx=5, pady=5)
        
        # Headers
        ttk.Label(drops_frame, text="Item ID", font=('Arial', 8, 'bold')).grid(row=1, column=0, padx=5)
        ttk.Label(drops_frame, text="Chance", font=('Arial', 8, 'bold')).grid(row=1, column=1, padx=5)
        ttk.Label(drops_frame, text="Qty Min", font=('Arial', 8, 'bold')).grid(row=1, column=2, padx=5)
        ttk.Label(drops_frame, text="Qty Max", font=('Arial', 8, 'bold')).grid(row=1, column=3, padx=5)
        
        # Add 8 drop entry rows
        for i in range(8):
            drop_row = 2 + i
            
            entry_id = ttk.Entry(drops_frame, width=25)
            entry_id.grid(row=drop_row, column=0, padx=2, pady=2)
            
            entry_chance = ttk.Entry(drops_frame, width=8)
            entry_chance.grid(row=drop_row, column=1, padx=2, pady=2)
            
            entry_qty_min = ttk.Entry(drops_frame, width=8)
            entry_qty_min.grid(row=drop_row, column=2, padx=2, pady=2)
            
            entry_qty_max = ttk.Entry(drops_frame, width=8)
            entry_qty_max.grid(row=drop_row, column=3, padx=2, pady=2)
            
            self.monster_drop_entries.append({
                'id': entry_id,
                'chance': entry_chance,
                'qty_min': entry_qty_min,
                'qty_max': entry_qty_max
            })
        
        # Save button
        ttk.Button(scrollable_frame, text="💾 Save Monster", command=self.save_monster,
                  style='Save.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load monsters
        self.load_monsters_list()
    
    def on_type_change(self, event=None):
        """Show/hide relevant stat frames based on item type"""
        item_type = self.item_fields['type'].get()
        
        if item_type == 'weapon':
            self.weapon_frame.grid()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid_remove()
            self.container_frame.grid_remove()
        elif item_type in ['armor', 'offhand', 'relic']:
            # All equipment types can use weapon and armor frames for stats
            self.weapon_frame.grid()  # Relics/offhand can have attack too
            self.armor_frame.grid()   # Can have defense too
            self.consumable_frame.grid_remove()
            self.container_frame.grid_remove()
        elif item_type == 'consumable':
            self.weapon_frame.grid_remove()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid()
            self.container_frame.grid_remove()
        elif item_type == 'container':
            self.weapon_frame.grid_remove()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid_remove()
            self.container_frame.grid()
        else:
            self.weapon_frame.grid_remove()
            self.armor_frame.grid_remove()
            self.consumable_frame.grid_remove()
            self.container_frame.grid_remove()
    
    def load_items_list(self):
        """Load items from items.json into the listbox"""
        self.items_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'items.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items_data = data.get('items', [])
                for item in self.items_data:
                    self.items_listbox.insert(tk.END, f"{item.get('id')} - {item.get('name')}")
                self.item_count_label.config(text=f"Items: {len(self.items_data)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load items: {e}")
            self.items_data = []
            self.item_count_label.config(text="Items: 0")
    
    def filter_items(self, *args):
        """Filter items list based on search"""
        search_term = self.item_search_var.get().lower()
        self.items_listbox.delete(0, tk.END)
        for item in self.items_data:
            item_text = f"{item.get('id')} - {item.get('name')}"
            if search_term in item_text.lower():
                self.items_listbox.insert(tk.END, item_text)
    
    def load_monsters_list(self):
        """Load monsters from monsters.json into the listbox"""
        self.monsters_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'monsters.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.monsters_data = data.get('enemies', [])
                for monster in self.monsters_data:
                    self.monsters_listbox.insert(tk.END, f"{monster.get('id')} - {monster.get('name')}")
                self.monster_count_label.config(text=f"Monsters: {len(self.monsters_data)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load monsters: {e}")
            self.monsters_data = []
            self.monster_count_label.config(text="Monsters: 0")
    
    def filter_monsters(self, *args):
        """Filter monsters list based on search"""
        search_term = self.monster_search_var.get().lower()
        self.monsters_listbox.delete(0, tk.END)
        for monster in self.monsters_data:
            monster_text = f"{monster.get('id')} - {monster.get('name')}"
            if search_term in monster_text.lower():
                self.monsters_listbox.insert(tk.END, monster_text)
    
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
        if item.get('magic_power'):
            self.item_fields['magic_power'].insert(0, str(item.get('magic_power')))
        if item.get('magic_penetration'):
            self.item_fields['magic_penetration'].insert(0, str(item.get('magic_penetration')))
        if item.get('lifesteal'):
            self.item_fields['lifesteal'].insert(0, str(item.get('lifesteal')))
        if item.get('agility'):
            self.item_fields['agility'].insert(0, str(item.get('agility')))
        if item.get('exp_gain'):
            self.item_fields['exp_gain'].insert(0, str(item.get('exp_gain')))
        if item.get('gold_gain'):
            self.item_fields['gold_gain'].insert(0, str(item.get('gold_gain')))
        
        # Armor stats
        if item.get('defense'):
            self.item_fields['defense'].insert(0, str(item.get('defense')))
            if item.get('penetration') and not self.item_fields['penetration_weapon'].get():
                self.item_fields['penetration_armor'].insert(0, str(item.get('penetration', '')))
        if item.get('max_hp'):
            self.item_fields['max_hp'].insert(0, str(item.get('max_hp')))
        if item.get('max_mana'):
            self.item_fields['max_mana'].insert(0, str(item.get('max_mana')))
        if item.get('mana_regen'):
            self.item_fields['mana_regen'].insert(0, str(item.get('mana_regen')))
        if item.get('hp_regen'):
            self.item_fields['hp_regen'].insert(0, str(item.get('hp_regen')))
        if item.get('dodge_chance'):
            self.item_fields['dodge_chance'].insert(0, str(item.get('dodge_chance')))
        
        # Consumable stats
        effect = item.get('effect', {})
        if effect.get('heal'):
            self.item_fields['heal'].insert(0, str(effect['heal']))
        if effect.get('heal_percent'):
            self.item_fields['heal_percent'].insert(0, str(effect['heal_percent']))
        if effect.get('restore_mana'):
            self.item_fields['restore_mana'].insert(0, str(effect['restore_mana']))
        
        # Container loot pool
        loot_pool = item.get('loot_pool', [])
        for i, loot_entry in enumerate(loot_pool[:5]):  # Max 5 entries in UI
            if 'item_id' in loot_entry:
                self.loot_pool_entries[i]['type'].set('item')
                self.loot_pool_entries[i]['id'].insert(0, loot_entry['item_id'])
            elif 'skill_id' in loot_entry:
                self.loot_pool_entries[i]['type'].set('skill')
                self.loot_pool_entries[i]['id'].insert(0, loot_entry['skill_id'])
            
            if 'chance' in loot_entry:
                self.loot_pool_entries[i]['chance'].insert(0, str(loot_entry['chance']))
            if 'qty' in loot_entry:
                self.loot_pool_entries[i]['qty'].insert(0, str(loot_entry['qty']))
        
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
        self.monster_fields['magic_def_base'].insert(0, str(monster.get('magic_def_base', '')))
        self.monster_fields['xp_base'].insert(0, str(monster.get('xp_base', '')))
        self.monster_fields['gold_base'].insert(0, str(monster.get('gold_base', '')))
        
        self.monster_fields['min_wave'].insert(0, str(monster.get('min_wave', '')))
        self.monster_fields['max_wave'].insert(0, str(monster.get('max_wave', '')))
        self.monster_fields['spawn_multiple'].insert(0, str(monster.get('spawn_on_wave_multiple_of', '')))
        self.monster_fields['image'].insert(0, str(monster.get('image', '')))
        
        # Load drops
        drops = monster.get('drops', [])
        for i, drop in enumerate(drops[:8]):  # Max 8 entries in UI
            if i < len(self.monster_drop_entries):
                self.monster_drop_entries[i]['id'].insert(0, drop.get('item_id', ''))
                self.monster_drop_entries[i]['chance'].insert(0, str(drop.get('chance', '')))
                self.monster_drop_entries[i]['qty_min'].insert(0, str(drop.get('qty_min', 1)))
                self.monster_drop_entries[i]['qty_max'].insert(0, str(drop.get('qty_max', 1)))
    
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
        
        # Clear loot pool entries
        for entry in self.loot_pool_entries:
            entry['type'].set('')
            entry['id'].delete(0, tk.END)
            entry['chance'].delete(0, tk.END)
            entry['qty'].delete(0, tk.END)
    
    def clear_monster_form(self):
        """Clear all monster form fields"""
        for key, field in self.monster_fields.items():
            if isinstance(field, (ttk.Entry, ttk.Combobox)):
                field.delete(0, tk.END)
        
        # Clear drop entries
        for entry in self.monster_drop_entries:
            entry['id'].delete(0, tk.END)
            entry['chance'].delete(0, tk.END)
            entry['qty_min'].delete(0, tk.END)
            entry['qty_max'].delete(0, tk.END)
    
    def new_item(self):
        """Clear form for new item creation"""
        self.clear_item_form()
        self.items_listbox.selection_clear(0, tk.END)
    
    def duplicate_item(self):
        """Duplicate the selected item with a new ID"""
        selection = self.items_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to duplicate")
            return
        
        # Item is already loaded in the form, just clear the ID to force new entry
        current_id = self.item_fields['id'].get()
        self.item_fields['id'].delete(0, tk.END)
        self.item_fields['id'].insert(0, f"{current_id}_copy")
        self.items_listbox.selection_clear(0, tk.END)
        messagebox.showinfo("Duplicate", "Item duplicated! Change the ID before saving.")
    
    def new_monster(self):
        """Clear form for new monster creation"""
        self.clear_monster_form()
        self.monsters_listbox.selection_clear(0, tk.END)
    
    def duplicate_monster(self):
        """Duplicate the selected monster with a new ID"""
        selection = self.monsters_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a monster to duplicate")
            return
        
        # Monster is already loaded in the form, just clear the ID to force new entry
        current_id = self.monster_fields['id'].get()
        self.monster_fields['id'].delete(0, tk.END)
        self.monster_fields['id'].insert(0, f"{current_id}_copy")
        self.monsters_listbox.selection_clear(0, tk.END)
        messagebox.showinfo("Duplicate", "Monster duplicated! Change the ID before saving.")
    
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
            if self.item_fields['magic_power'].get():
                item['magic_power'] = int(self.item_fields['magic_power'].get())
            if self.item_fields['magic_penetration'].get():
                item['magic_penetration'] = float(self.item_fields['magic_penetration'].get())
            if self.item_fields['lifesteal'].get():
                item['lifesteal'] = float(self.item_fields['lifesteal'].get())
            if self.item_fields['agility'].get():
                item['agility'] = int(self.item_fields['agility'].get())
            if self.item_fields['exp_gain'].get():
                item['exp_gain'] = float(self.item_fields['exp_gain'].get())
            if self.item_fields['gold_gain'].get():
                item['gold_gain'] = float(self.item_fields['gold_gain'].get())
        
        # Armor/defensive stats
        if itype in ['armor', 'offhand', 'relic']:
            if self.item_fields['defense'].get():
                item['defense'] = int(self.item_fields['defense'].get())
            if self.item_fields['penetration_armor'].get() and not item.get('penetration'):
                item['penetration'] = float(self.item_fields['penetration_armor'].get())
            if self.item_fields['max_hp'].get():
                item['max_hp'] = int(self.item_fields['max_hp'].get())
            if self.item_fields['max_mana'].get():
                item['max_mana'] = int(self.item_fields['max_mana'].get())
            if self.item_fields['mana_regen'].get():
                item['mana_regen'] = int(self.item_fields['mana_regen'].get())
            if self.item_fields['hp_regen'].get():
                item['hp_regen'] = float(self.item_fields['hp_regen'].get())
            if self.item_fields['dodge_chance'].get():
                item['dodge_chance'] = float(self.item_fields['dodge_chance'].get())
        
        # Consumable stats
        if itype == 'consumable':
            effect = {}
            if self.item_fields['heal'].get():
                effect['heal'] = int(self.item_fields['heal'].get())
            if self.item_fields['heal_percent'].get():
                effect['heal_percent'] = float(self.item_fields['heal_percent'].get())
            if self.item_fields['restore_mana'].get():
                effect['restore_mana'] = int(self.item_fields['restore_mana'].get())
            if effect:
                item['effect'] = effect
        
        # Container loot pool
        if itype == 'container':
            loot_pool = []
            for entry in self.loot_pool_entries:
                entry_type = entry['type'].get()
                entry_id = entry['id'].get()
                entry_chance = entry['chance'].get()
                entry_qty = entry['qty'].get()
                
                if entry_id and entry_chance:  # Must have ID and chance
                    loot_entry = {}
                    if entry_type == 'item':
                        loot_entry['item_id'] = entry_id
                    elif entry_type == 'skill':
                        loot_entry['skill_id'] = entry_id
                    else:
                        continue  # Skip invalid type
                    
                    loot_entry['chance'] = float(entry_chance)
                    if entry_qty:
                        loot_entry['qty'] = int(entry_qty)
                    
                    loot_pool.append(loot_entry)
            
            if loot_pool:
                item['loot_pool'] = loot_pool
        
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
        if self.monster_fields['magic_def_base'].get():
            monster['magic_def_base'] = int(self.monster_fields['magic_def_base'].get())
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
        
        # Drops
        drops = []
        for entry in self.monster_drop_entries:
            item_id = entry['id'].get()
            chance = entry['chance'].get()
            
            if item_id and chance:  # Must have item_id and chance
                drop_entry = {
                    'item_id': item_id,
                    'chance': float(chance)
                }
                
                qty_min = entry['qty_min'].get()
                qty_max = entry['qty_max'].get()
                
                if qty_min:
                    drop_entry['qty_min'] = int(qty_min)
                else:
                    drop_entry['qty_min'] = 1
                    
                if qty_max:
                    drop_entry['qty_max'] = int(qty_max)
                else:
                    drop_entry['qty_max'] = 1
                
                drops.append(drop_entry)
        
        if drops:
            monster['drops'] = drops
        
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
                # Preserve attacks if they exist (drops are now from UI)
                if 'attacks' in existing and not monster.get('attacks'):
                    monster['attacks'] = existing['attacks']
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
    
    def setup_skills_tab(self):
        """Setup the Skills tab with form fields"""
        # Left side - Skill list
        left_frame = ttk.Frame(self.skills_frame)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Existing Skills:", font=('Arial', 10, 'bold')).pack()
        
        self.skills_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.skills_listbox.pack(fill='both', expand=True)
        self.skills_listbox.bind('<<ListboxSelect>>', self.load_selected_skill)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Skill", command=self.new_skill).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_skill).pack(side='left', padx=2)
        
        # Right side - Skill editor
        right_frame = ttk.Frame(self.skills_frame)
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
        
        # Skill fields
        self.skill_fields = {}
        row = 0
        
        # ID
        ttk.Label(scrollable_frame, text="ID*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.skill_fields['id'] = ttk.Entry(scrollable_frame, width=40)
        self.skill_fields['id'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Name
        ttk.Label(scrollable_frame, text="Name*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.skill_fields['name'] = ttk.Entry(scrollable_frame, width=40)
        self.skill_fields['name'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Description
        ttk.Label(scrollable_frame, text="Description:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.skill_fields['description'] = ttk.Entry(scrollable_frame, width=40)
        self.skill_fields['description'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Type
        ttk.Label(scrollable_frame, text="Type*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.skill_fields['type'] = ttk.Combobox(scrollable_frame, width=37, 
                                                values=['damage', 'heal', 'buff', 'debuff', 'counter'])
        self.skill_fields['type'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Element
        ttk.Label(scrollable_frame, text="Element:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.skill_fields['element'] = ttk.Combobox(scrollable_frame, width=37,
                                                   values=['physical', 'arcane', 'fire', 'ice', 'lightning', 'dark', 'light', 'neutral'])
        self.skill_fields['element'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Stats frame
        stats_frame = ttk.LabelFrame(scrollable_frame, text="Skill Stats")
        stats_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(stats_frame, text="Mana Cost:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.skill_fields['mana_cost'] = ttk.Entry(stats_frame, width=15)
        self.skill_fields['mana_cost'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Power:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.skill_fields['power'] = ttk.Entry(stats_frame, width=15)
        self.skill_fields['power'].grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Scaling Stat:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        self.skill_fields['scaling_stat'] = ttk.Combobox(stats_frame, width=12,
                                                        values=['atk', 'magic_power', 'defense'])
        self.skill_fields['scaling_stat'].grid(row=2, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Penetration:").grid(row=3, column=0, sticky='w', padx=5, pady=3)
        self.skill_fields['penetration'] = ttk.Entry(stats_frame, width=15)
        self.skill_fields['penetration'].grid(row=3, column=1, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Cooldown:").grid(row=0, column=2, sticky='w', padx=5, pady=3)
        self.skill_fields['cooldown'] = ttk.Entry(stats_frame, width=15)
        self.skill_fields['cooldown'].grid(row=0, column=3, padx=5, pady=3)
        
        ttk.Label(stats_frame, text="Target:").grid(row=1, column=2, sticky='w', padx=5, pady=3)
        self.skill_fields['target'] = ttk.Combobox(stats_frame, width=12,
                                                  values=['single', 'self', 'all'])
        self.skill_fields['target'].grid(row=1, column=3, padx=5, pady=3)
        
        # Unlock requirements frame
        unlock_frame = ttk.LabelFrame(scrollable_frame, text="Unlock Requirements")
        unlock_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        ttk.Label(unlock_frame, text="Level Required:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        self.skill_fields['unlock_level'] = ttk.Entry(unlock_frame, width=15)
        self.skill_fields['unlock_level'].grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(unlock_frame, text="Item Required:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        self.skill_fields['unlock_item'] = ttk.Entry(unlock_frame, width=30)
        self.skill_fields['unlock_item'].grid(row=1, column=1, padx=5, pady=3)
        
        # Save button
        ttk.Button(scrollable_frame, text="💾 Save Skill", command=self.save_skill,
                  style='Save.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load skills
        self.load_skills_list()
    
    def load_skills_list(self):
        """Load skills from skills.json into the listbox"""
        self.skills_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'skills.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.skills_data = data.get('skills', [])
                for skill in self.skills_data:
                    self.skills_listbox.insert(tk.END, f"{skill.get('id')} - {skill.get('name', '')}")
        except FileNotFoundError:
            self.skills_data = []
            messagebox.showwarning("Warning", "skills.json not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load skills: {e}")
    
    def load_selected_skill(self, event=None):
        """Load selected skill into editor"""
        selection = self.skills_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        skill = self.skills_data[index]
        
        # Clear form
        self.clear_skill_form()
        
        # Load basic fields
        self.skill_fields['id'].insert(0, skill.get('id', ''))
        self.skill_fields['name'].insert(0, skill.get('name', ''))
        self.skill_fields['description'].insert(0, skill.get('description', ''))
        self.skill_fields['type'].set(skill.get('type', ''))
        self.skill_fields['element'].set(skill.get('element', ''))
        
        # Load stats
        if skill.get('mana_cost') is not None:
            self.skill_fields['mana_cost'].insert(0, str(skill['mana_cost']))
        if skill.get('power') is not None:
            self.skill_fields['power'].insert(0, str(skill['power']))
        if skill.get('scaling_stat'):
            self.skill_fields['scaling_stat'].set(skill['scaling_stat'])
        if skill.get('penetration') is not None:
            self.skill_fields['penetration'].insert(0, str(skill['penetration']))
        if skill.get('cooldown') is not None:
            self.skill_fields['cooldown'].insert(0, str(skill['cooldown']))
        if skill.get('target'):
            self.skill_fields['target'].set(skill['target'])
        
        # Load unlock requirements
        unlock_req = skill.get('unlock_requirements', {})
        if unlock_req.get('level'):
            self.skill_fields['unlock_level'].insert(0, str(unlock_req['level']))
        if unlock_req.get('item_equipped'):
            self.skill_fields['unlock_item'].insert(0, unlock_req['item_equipped'])
    
    def clear_skill_form(self):
        """Clear all skill form fields"""
        for key, field in self.skill_fields.items():
            if isinstance(field, (ttk.Entry, ttk.Combobox)):
                field.delete(0, tk.END)
    
    def new_skill(self):
        """Clear form for new skill creation"""
        self.clear_skill_form()
        self.skills_listbox.selection_clear(0, tk.END)
    
    def save_skill(self):
        """Save skill to skills.json"""
        # Validate required fields
        if not self.skill_fields['id'].get() or not self.skill_fields['name'].get() or not self.skill_fields['type'].get():
            messagebox.showerror("Error", "ID, Name, and Type are required!")
            return
        
        # Build skill dict
        skill = {
            'id': self.skill_fields['id'].get(),
            'name': self.skill_fields['name'].get(),
            'type': self.skill_fields['type'].get(),
        }
        
        if self.skill_fields['description'].get():
            skill['description'] = self.skill_fields['description'].get()
        
        if self.skill_fields['element'].get():
            skill['element'] = self.skill_fields['element'].get()
        
        # Stats
        if self.skill_fields['mana_cost'].get():
            skill['mana_cost'] = int(self.skill_fields['mana_cost'].get())
        if self.skill_fields['power'].get():
            skill['power'] = int(self.skill_fields['power'].get())
        if self.skill_fields['scaling_stat'].get():
            skill['scaling_stat'] = self.skill_fields['scaling_stat'].get()
        if self.skill_fields['penetration'].get():
            skill['penetration'] = float(self.skill_fields['penetration'].get())
        if self.skill_fields['cooldown'].get():
            skill['cooldown'] = int(self.skill_fields['cooldown'].get())
        if self.skill_fields['target'].get():
            skill['target'] = self.skill_fields['target'].get()
        
        # Unlock requirements
        unlock_req = {}
        if self.skill_fields['unlock_level'].get():
            unlock_req['level'] = int(self.skill_fields['unlock_level'].get())
        if self.skill_fields['unlock_item'].get():
            unlock_req['item_equipped'] = self.skill_fields['unlock_item'].get()
        if unlock_req:
            skill['unlock_requirements'] = unlock_req
        
        # Default empty fields
        if 'effectiveness' not in skill:
            skill['effectiveness'] = {}
        if 'effects' not in skill:
            skill['effects'] = []
        
        # Find if updating or creating new
        skill_id = skill['id']
        found = False
        for i, existing in enumerate(self.skills_data):
            if existing.get('id') == skill_id:
                self.skills_data[i] = skill
                found = True
                break
        
        if not found:
            self.skills_data.append(skill)
        
        # Save to file
        try:
            with open(self.data_path / 'skills.json', 'w', encoding='utf-8') as f:
                json.dump({'skills': self.skills_data}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Skill '{skill['name']}' saved!")
            self.load_skills_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save skill: {e}")
    
    def delete_skill(self):
        """Delete selected skill"""
        selection = self.skills_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No skill selected")
            return
        
        index = selection[0]
        skill = self.skills_data[index]
        
        if messagebox.askyesno("Confirm Delete", f"Delete skill '{skill.get('name')}'?"):
            try:
                self.skills_data.pop(index)
                with open(self.data_path / 'skills.json', 'w', encoding='utf-8') as f:
                    json.dump({'skills': self.skills_data}, f, indent=2, ensure_ascii=False)
                self.load_skills_list()
                self.clear_skill_form()
                messagebox.showinfo("Success", "Skill deleted!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete skill: {e}")
    
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
        ttk.Button(scrollable_frame, text="💾 Save Zone", command=self.save_zone,
                  style='Save.TButton').grid(row=row, column=0, columnspan=2, pady=20)
        
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
    
    def setup_recipes_tab(self):
        """Setup the Recipes tab with form fields"""
        # Left side - Recipe list
        left_frame = ttk.Frame(self.recipes_frame)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Existing Recipes:", font=('Arial', 10, 'bold')).pack()
        
        self.recipes_listbox = tk.Listbox(left_frame, width=30, height=25)
        self.recipes_listbox.pack(fill='both', expand=True)
        self.recipes_listbox.bind('<<ListboxSelect>>', self.load_selected_recipe)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="New Recipe", command=self.new_recipe).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_recipe).pack(side='left', padx=2)
        
        # Right side - Recipe editor
        right_frame = ttk.Frame(self.recipes_frame)
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
        
        # Recipe fields
        self.recipe_fields = {}
        row = 0
        
        # ID
        ttk.Label(scrollable_frame, text="ID*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['id'] = ttk.Entry(scrollable_frame, width=40)
        self.recipe_fields['id'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Name
        ttk.Label(scrollable_frame, text="Name*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['name'] = ttk.Entry(scrollable_frame, width=40)
        self.recipe_fields['name'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Description
        ttk.Label(scrollable_frame, text="Description:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['description'] = ttk.Entry(scrollable_frame, width=40)
        self.recipe_fields['description'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Category
        ttk.Label(scrollable_frame, text="Category*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['category'] = ttk.Combobox(scrollable_frame, width=37,
                                                      values=['weapon', 'armor', 'consumable', 'material', 'misc'])
        self.recipe_fields['category'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Result Item ID
        ttk.Label(scrollable_frame, text="Result Item ID*:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['result_item_id'] = ttk.Entry(scrollable_frame, width=40)
        self.recipe_fields['result_item_id'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Result Quantity
        ttk.Label(scrollable_frame, text="Result Quantity:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['result_quantity'] = ttk.Entry(scrollable_frame, width=40)
        self.recipe_fields['result_quantity'].insert(0, '1')
        self.recipe_fields['result_quantity'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Required Level
        ttk.Label(scrollable_frame, text="Required Level:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        self.recipe_fields['required_level'] = ttk.Entry(scrollable_frame, width=40)
        self.recipe_fields['required_level'].insert(0, '1')
        self.recipe_fields['required_level'].grid(row=row, column=1, pady=5)
        row += 1
        
        # Ingredients section
        ingredients_frame = ttk.LabelFrame(scrollable_frame, text="Ingredients")
        ingredients_frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1
        
        self.recipe_fields['ingredients'] = []
        self.ingredient_entries = []
        
        # Add button for ingredients
        ttk.Button(ingredients_frame, text="Add Ingredient", command=self.add_ingredient_field).pack(pady=5)
        
        # Container for ingredient rows
        self.ingredients_container = ttk.Frame(ingredients_frame)
        self.ingredients_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Save button
        save_btn = ttk.Button(scrollable_frame, text="💾 Save Recipe", command=self.save_recipe, style='Save.TButton')
        save_btn.grid(row=row, column=0, columnspan=2, pady=20)
        
        # Load recipes
        self.load_recipes_list()
    
    def add_ingredient_field(self):
        """Add a new ingredient input row"""
        row_frame = ttk.Frame(self.ingredients_container)
        row_frame.pack(fill='x', pady=2)
        
        ttk.Label(row_frame, text="Item ID:", width=10).pack(side='left', padx=2)
        item_id_entry = ttk.Entry(row_frame, width=20)
        item_id_entry.pack(side='left', padx=2)
        
        ttk.Label(row_frame, text="Qty:", width=5).pack(side='left', padx=2)
        qty_entry = ttk.Entry(row_frame, width=10)
        qty_entry.insert(0, '1')
        qty_entry.pack(side='left', padx=2)
        
        # Remove button
        def remove_this():
            row_frame.destroy()
            self.ingredient_entries.remove((item_id_entry, qty_entry))
        
        ttk.Button(row_frame, text="Remove", command=remove_this).pack(side='left', padx=2)
        
        self.ingredient_entries.append((item_id_entry, qty_entry))
    
    def load_recipes_list(self):
        """Load recipes from recipes.json into listbox"""
        self.recipes_listbox.delete(0, tk.END)
        try:
            with open(self.data_path / 'recipes.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.recipes_data = data.get('recipes', [])
                for recipe in self.recipes_data:
                    display_name = f"{recipe.get('name', 'Unnamed')} ({recipe.get('id', 'no-id')})"
                    self.recipes_listbox.insert(tk.END, display_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recipes: {e}")
            self.recipes_data = []
    
    def load_selected_recipe(self, event):
        """Load selected recipe into form"""
        selection = self.recipes_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        recipe = self.recipes_data[idx]
        
        # Clear form
        self.clear_recipe_form()
        
        # Populate basic fields
        self.recipe_fields['id'].insert(0, recipe.get('id', ''))
        self.recipe_fields['name'].insert(0, recipe.get('name', ''))
        self.recipe_fields['description'].insert(0, recipe.get('description', ''))
        self.recipe_fields['category'].set(recipe.get('category', 'misc'))
        self.recipe_fields['result_item_id'].insert(0, recipe.get('result_item_id', ''))
        self.recipe_fields['result_quantity'].delete(0, tk.END)
        self.recipe_fields['result_quantity'].insert(0, str(recipe.get('result_quantity', 1)))
        self.recipe_fields['required_level'].delete(0, tk.END)
        self.recipe_fields['required_level'].insert(0, str(recipe.get('required_level', 1)))
        
        # Load ingredients
        for ingredient in recipe.get('ingredients', []):
            self.add_ingredient_field()
            item_id_entry, qty_entry = self.ingredient_entries[-1]
            item_id_entry.insert(0, ingredient.get('item_id', ''))
            qty_entry.delete(0, tk.END)
            qty_entry.insert(0, str(ingredient.get('quantity', 1)))
    
    def clear_recipe_form(self):
        """Clear all recipe form fields"""
        for key in ['id', 'name', 'description', 'result_item_id']:
            self.recipe_fields[key].delete(0, tk.END)
        self.recipe_fields['category'].set('')
        self.recipe_fields['result_quantity'].delete(0, tk.END)
        self.recipe_fields['result_quantity'].insert(0, '1')
        self.recipe_fields['required_level'].delete(0, tk.END)
        self.recipe_fields['required_level'].insert(0, '1')
        
        # Clear ingredient fields
        for widget in self.ingredients_container.winfo_children():
            widget.destroy()
        self.ingredient_entries = []
    
    def new_recipe(self):
        """Create a new recipe"""
        self.clear_recipe_form()
    
    def save_recipe(self):
        """Save current recipe to recipes.json"""
        # Validate required fields
        if not self.recipe_fields['id'].get():
            messagebox.showwarning("Warning", "Recipe ID is required")
            return
        if not self.recipe_fields['name'].get():
            messagebox.showwarning("Warning", "Recipe name is required")
            return
        if not self.recipe_fields['result_item_id'].get():
            messagebox.showwarning("Warning", "Result item ID is required")
            return
        
        # Parse numeric fields
        try:
            result_quantity = int(self.recipe_fields['result_quantity'].get() or '1')
            required_level = int(self.recipe_fields['required_level'].get() or '1')
        except ValueError:
            messagebox.showerror("Error", "Result quantity and required level must be integers")
            return
        
        # Build ingredients list
        ingredients = []
        for item_id_entry, qty_entry in self.ingredient_entries:
            item_id = item_id_entry.get().strip()
            if item_id:
                try:
                    qty = int(qty_entry.get() or '1')
                    ingredients.append({
                        'item_id': item_id,
                        'quantity': qty
                    })
                except ValueError:
                    messagebox.showerror("Error", f"Invalid quantity for ingredient {item_id}")
                    return
        
        if not ingredients:
            messagebox.showwarning("Warning", "At least one ingredient is required")
            return
        
        # Build recipe dict
        recipe = {
            'id': self.recipe_fields['id'].get(),
            'name': self.recipe_fields['name'].get(),
            'description': self.recipe_fields['description'].get(),
            'category': self.recipe_fields['category'].get() or 'misc',
            'result_item_id': self.recipe_fields['result_item_id'].get(),
            'result_quantity': result_quantity,
            'required_level': required_level,
            'ingredients': ingredients
        }
        
        # Find if updating or creating new
        recipe_id = recipe['id']
        found = False
        for i, existing in enumerate(self.recipes_data):
            if existing.get('id') == recipe_id:
                self.recipes_data[i] = recipe
                found = True
                break
        
        if not found:
            self.recipes_data.append(recipe)
        
        # Save to file
        try:
            with open(self.data_path / 'recipes.json', 'w', encoding='utf-8') as f:
                json.dump({'recipes': self.recipes_data}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Recipe '{recipe['name']}' saved successfully!")
            self.load_recipes_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipe: {e}")
    
    def delete_recipe(self):
        """Delete selected recipe"""
        selection = self.recipes_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a recipe to delete")
            return
        
        idx = selection[0]
        recipe = self.recipes_data[idx]
        
        if messagebox.askyesno("Confirm Delete", f"Delete recipe '{recipe.get('name')}'?"):
            self.recipes_data.pop(idx)
            try:
                with open(self.data_path / 'recipes.json', 'w', encoding='utf-8') as f:
                    json.dump({'recipes': self.recipes_data}, f, indent=2, ensure_ascii=False)
                self.load_recipes_list()
                self.clear_recipe_form()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete recipe: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AdminInterface(root)
    root.mainloop()
