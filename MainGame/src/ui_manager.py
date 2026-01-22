# src/ui_manager.py
import pygame
try:
    # when running as top-level script
    from shop import Shop
except Exception:
    # when running as package (e.g., src.ui_manager)
    from .shop import Shop


class UIManager:
    def __init__(self, screen, assets_path=None, data_path=None):
        self.screen = screen
        self.assets_path = assets_path
        self.data_path = data_path
        self.buttons = []
        # State for allocation UI
        self.allocation_open = False
        self.alloc_buttons = []
        # equipment UI buttons
        self.equip_buttons = []
        # Pré-créer les polices pour éviter de les recréer à chaque frame
        self.title_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        # Full-window background image (optional)
        self.full_bg_image = None
        try:
            if self.assets_path:
                bg_path = self.assets_path / "images" / "backgrounds" / "default_bg.png"
                if bg_path.exists():
                    self.full_bg_image = pygame.image.load(str(bg_path)).convert()
        except Exception:
            self.full_bg_image = None
        # Charger une image de panneau UI si présente
        self.panel_image = None
        try:
            if self.assets_path:
                panel_path = self.assets_path / "images" / "backgrounds" / "ui_panel.png"
                if panel_path.exists():
                    self.panel_image = pygame.image.load(str(panel_path)).convert_alpha()
        except Exception:
            # ignore any load errors and fallback to drawing a rectangle
            self.panel_image = None
        # shop loader for item lookup
        try:
            if self.data_path:
                self.shop_loader = Shop(self.data_path)
            else:
                self.shop_loader = None
        except Exception:
            self.shop_loader = None
        # Unified character sheet modal with tabs
        self.character_sheet_open = False
        self.character_sheet_tab = 'equipment'  # 'equipment', 'inventory', 'stats'
        self.character_sheet_buttons = []
        self.inventory_cells = []
        self.inventory_selected = None
        self.inventory_page = 0
        self.stats_page = 0
        self.character_sheet_open_rect = None
        # Dragging state for moveable character sheet
        self.character_sheet_dragging = False
        self.character_sheet_drag_offset = (0, 0)
        self.character_sheet_pos = None  # Will be (x, y) when set
        # Floating damage texts: list of dicts {text, pos, start_time, duration, color, alpha, dy}
        self.floats = []

    def _blit_text_outlined(self, surface, font, text, pos, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=False):
        """Render text with a simple outline by drawing the outline color around the text.

        Returns the rect where the final text was blitted.
        """
        # render main and outline surfaces
        try:
            main_surf = font.render(text, True, fg)
            if outline_width <= 0:
                r = main_surf.get_rect()
                if center:
                    r.center = pos
                else:
                    r.topleft = pos
                surface.blit(main_surf, r)
                return r

            outline_surf = font.render(text, True, outline)
            # draw outline by blitting outline_surf at offsets
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx == 0 and dy == 0:
                        continue
                    r = outline_surf.get_rect()
                    if center:
                        r.center = (pos[0] + dx, pos[1] + dy)
                    else:
                        r.topleft = (pos[0] + dx, pos[1] + dy)
                    surface.blit(outline_surf, r)

            # finally blit main text
            r = main_surf.get_rect()
            if center:
                r.center = pos
            else:
                r.topleft = pos
            surface.blit(main_surf, r)
            return r
        except Exception:
            # fallback simple render
            s = font.render(text, True, fg)
            r = s.get_rect()
            if center:
                r.center = pos
            else:
                r.topleft = pos
            surface.blit(s, r)
            return r

    def set_actions(self, battle):
        screen_width, screen_height = self.screen.get_size()
        # Bouton d'attaque (stocke la référence à la méthode du battle)
        self.buttons = [
            {
                "rect": pygame.Rect(screen_width - 300, screen_height - 100, 200, 60),
                "label": "Attaquer",
                "action": battle.player_attack,
            },
        ]

    # allocation buttons are created dynamically in draw when needed

    def handle_event(self, event):
        # Toggle allocation UI with Tab
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.allocation_open = not self.allocation_open
            return
        
        # Toggle character sheet with 'C' key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            self.character_sheet_open = not self.character_sheet_open
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check character sheet buttons first (close, tabs, etc.) before dragging
            for btn in getattr(self, 'character_sheet_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return
            
            # Check if dragging character sheet title bar
            if getattr(self, 'character_sheet_open', False) and hasattr(self, 'character_sheet_title_bar'):
                if self.character_sheet_title_bar.collidepoint(event.pos):
                    self.character_sheet_dragging = True
                    pos = self.character_sheet_pos or ((self.screen.get_width() - 700) // 2, (self.screen.get_height() - 500) // 2)
                    self.character_sheet_drag_offset = (event.pos[0] - pos[0], event.pos[1] - pos[1])
                    return
            
            # check main buttons
            for btn in self.buttons:
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return

            # check allocation buttons
            for btn in getattr(self, 'alloc_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    # action is a lambda that accepts no args
                    btn["action"]()
                    return
            # check equipment buttons
            for btn in getattr(self, 'equip_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return

            # character sheet modal buttons (tabs, close, inventory cells, etc.)
            for btn in getattr(self, 'character_sheet_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return
            for cell in getattr(self, 'inventory_cells', []):
                if cell['rect'].collidepoint(event.pos):
                    # select this item
                    self.inventory_selected = cell['item_id']
                    return

            # character sheet open/close button on main panel
            if getattr(self, 'character_sheet_open_rect', None) and self.character_sheet_open_rect.collidepoint(event.pos):
                self.character_sheet_open = not self.character_sheet_open
                return
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.character_sheet_dragging = False
        
        if event.type == pygame.MOUSEMOTION:
            if getattr(self, 'character_sheet_dragging', False):
                new_x = event.pos[0] - self.character_sheet_drag_offset[0]
                new_y = event.pos[1] - self.character_sheet_drag_offset[1]
                # Clamp to screen bounds
                new_x = max(0, min(new_x, self.screen.get_width() - 700))
                new_y = max(0, min(new_y, self.screen.get_height() - 500))
                self.character_sheet_pos = (new_x, new_y)

    def update(self, player, battle):
        # Process battle damage events into floating texts
        try:
            if battle and hasattr(battle, 'damage_events') and battle.damage_events:
                # create a float for each event
                for ev in battle.damage_events:
                    text = f"-{ev.get('amount', 0)}"
                    if ev.get('is_crit'):
                        color = (255, 60, 60)
                    else:
                        color = (255, 180, 100)
                    # position: above enemy or player sprite area; default positions
                    screen_w, screen_h = self.screen.get_size()
                    if ev.get('target') == 'enemy' and getattr(battle, 'enemy', None):
                        # place above enemy UI area (approx center-right screen)
                        pos = (screen_w // 2 + 100, screen_h // 2 - 80)
                    else:
                        # player damage near player sprite location
                        pos = (120, 480)

                    self.floats.append({
                        'text': text,
                        'pos': list(pos),
                        'start': pygame.time.get_ticks() / 1000.0,
                        'duration': 1.2,
                        'color': color,
                        'alpha': 255,
                        'dy': -1.0,
                    })
                # clear events after processing
                battle.damage_events.clear()
        except Exception:
            pass

        # update existing floats (position and alpha)
        now = pygame.time.get_ticks() / 1000.0
        new_floats = []
        for f in self.floats:
            elapsed = now - f['start']
            if elapsed >= f['duration']:
                continue
            # move upward over time
            f['pos'][1] += f['dy'] * (1 + elapsed * 8)
            # reduce alpha
            f['alpha'] = int(max(0, 255 * (1 - (elapsed / f['duration']))))
            new_floats.append(f)
        self.floats = new_floats
        return

    def draw(self, player=None, battle=None):
        # Draw a background panel for UI (image if available, otherwise a semi-transparent rect)
        screen_w, screen_h = self.screen.get_size()
        # larger panel to avoid content overlap - extend to bottom of screen
        panel_w = 420
        panel_h = screen_h - 20  # 10px margin top and bottom
        panel_x = 10
        panel_y = 10
        if self.panel_image:
            # Crop the image to maintain aspect ratio without repeating
            # Get original dimensions
            orig_w, orig_h = self.panel_image.get_size()
            # Scale width to match panel_w while maintaining aspect ratio
            scale_factor = panel_w / orig_w
            scaled_h = int(orig_h * scale_factor)
            scaled_img = pygame.transform.smoothscale(self.panel_image, (panel_w, scaled_h))
            
            # Only blit once - crop at panel_h if image is taller, or just show what we have if shorter
            if scaled_h > panel_h:
                # Image is taller than panel - crop it
                cropped_img = scaled_img.subsurface(pygame.Rect(0, 0, panel_w, panel_h))
                self.screen.blit(cropped_img, (panel_x, panel_y))
            else:
                # Image is shorter than panel - just show it once
                self.screen.blit(scaled_img, (panel_x, panel_y))
        else:
            s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            s.fill((20, 20, 30, 200))  # semi-transparent dark panel
            # rounded rect isn't in older pygame, draw basic rect for compatibility
            self.screen.blit(s, (panel_x, panel_y))

        # Dessine les boutons
        for btn in self.buttons:
            pygame.draw.rect(self.screen, (100, 100, 250), btn["rect"], border_radius=8)
            # outlined label
            self._blit_text_outlined(self.screen, self.title_font, btn["label"], btn["rect"].center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)

        # Affichage des infos joueur / ennemi
        x = panel_x + 12
        y = panel_y + 12
        line_h = 28

        if player is not None:
            self._blit_text_outlined(self.screen, self.small_font, f"Player HP: {player.hp}/{player.max_hp}", (x, y), fg=(255,255,255), outline=(0,0,0), outline_width=2)
            y += line_h

        if battle is not None and getattr(battle, "enemy", None):
            enemy = battle.enemy
            self._blit_text_outlined(self.screen, self.small_font, f"Enemy: {getattr(enemy, 'name', 'Unknown')}", (x, y), fg=(255,200,200), outline=(0,0,0), outline_width=2)
            y += line_h

            self._blit_text_outlined(self.screen, self.small_font, f"Enemy HP: {enemy.hp}/{enemy.max_hp}", (x, y), fg=(255,150,150), outline=(0,0,0), outline_width=2)
            y += line_h

            # Barre de vie
            bar_x, bar_y = x, y
            bar_width, bar_height = 200, 20
            hp_ratio = (enemy.hp / enemy.max_hp) if getattr(enemy, "max_hp", 1) > 0 else 0
            pygame.draw.rect(self.screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
            self._blit_text_outlined(self.screen, self.small_font, f"{enemy.hp}/{enemy.max_hp}", (bar_x + bar_width + 10, bar_y), fg=(255,255,255), outline=(0,0,0), outline_width=2)
            y += bar_height + 10

        # Stats joueur (gold, level)
        if player is not None:
            gold = getattr(player, "gold", 0)
            self._blit_text_outlined(self.screen, self.small_font, f"Gold: {gold}", (x, y), fg=(255,215,0), outline=(0,0,0), outline_width=2)
            y += line_h

            level = getattr(player, "level", 1)
            self._blit_text_outlined(self.screen, self.small_font, f"Level: {level}", (x, y), fg=(200,200,255), outline=(0,0,0), outline_width=2)
            y += line_h

        # Vague
        if battle is not None and hasattr(battle, "wave"):
            self._blit_text_outlined(self.screen, self.small_font, f"Wave: {battle.wave}", (x, y), fg=(255,255,180), outline=(0,0,0), outline_width=2)

        # Equipment display - Multiple slots
        self.equip_buttons = []
        y += line_h
        
        # Define slot display order and labels
        equipment_slots = [
            ('weapon', 'Weapon'),
            ('armor', 'Armor'),
            ('offhand', 'Offhand'),
            ('relic1', 'Relic 1'),
            ('relic2', 'Relic 2'),
            ('relic3', 'Relic 3')
        ]
        
        for slot_key, slot_label in equipment_slots:
            item_id = player.equipment.get(slot_key) if player else None
            item_data = self.shop_loader.find_item(item_id) if getattr(self, 'shop_loader', None) and item_id else None
            item_name = item_data.get('name') if item_data else (item_id or 'None')
            
            # Slot name and item
            slot_text = f"{slot_label}: {item_name}"
            self._blit_text_outlined(self.screen, self.small_font, slot_text, (x, y), fg=(220,220,220), outline=(0,0,0), outline_width=2)
            
            # Unequip button (only if something is equipped)
            if item_id:
                unequip_rect = pygame.Rect(x + 200, y - 4, 80, 24)
                pygame.draw.rect(self.screen, (180, 80, 80), unequip_rect, border_radius=4)
                unequip_text = self.small_font.render("Unequip", True, (0, 0, 0))
                self.screen.blit(unequip_text, unequip_text.get_rect(center=unequip_rect.center))
                self.equip_buttons.append({"rect": unequip_rect, "action": (lambda p=player, s=slot_key: p.unequip(s))})
                
                # Draw item icon if available
                if item_data and self.assets_path:
                    icon_path = self.assets_path / 'images' / 'items' / f"{item_data.get('id')}.png"
                    if icon_path.exists():
                        ico = pygame.image.load(str(icon_path)).convert_alpha()
                        ico = pygame.transform.smoothscale(ico, (20, 20))
                        self.screen.blit(ico, (x + 165, y + 2))
            
            y += line_h

        # Allocation UI (si le joueur a des points non dépensés ou si l'UI est ouverte)
        self.alloc_buttons = []
        if player is not None and (getattr(player, 'unspent_points', 0) > 0 or self.allocation_open):
            y += line_h
            up = getattr(player, 'unspent_points', 0)
            self._blit_text_outlined(self.screen, self.small_font, f"Unspent points: {up}", (x, y), fg=(255,220,180), outline=(0,0,0), outline_width=2)
            y += line_h

            # Create 3 small buttons: Atk, Def, HP
            btn_w = 80
            btn_h = 28
            spacing = 10
            bx = x
            by = y

            def make_alloc(label, stat):
                rect = pygame.Rect(bx, by, btn_w, btn_h)
                def action(stat=stat):
                    if player.spend_point(stat):
                        # no-op; player is updated in place
                        pass
                return {"rect": rect, "label": label, "action": action}

            labels = [("+ATK", "atk"), ("+DEF", "def"), ("+HP", "hp"), ("+AGI", "agi")]
            for i, (lab, st) in enumerate(labels):
                btn_rect = pygame.Rect(bx + i * (btn_w + spacing), by, btn_w, btn_h)
                pygame.draw.rect(self.screen, (80, 160, 80), btn_rect, border_radius=6)
                # black label on light button
                t = self.small_font.render(lab, True, (0, 0, 0))
                trect = t.get_rect(center=btn_rect.center)
                self.screen.blit(t, trect)
                # store for click handling
                self.alloc_buttons.append({"rect": btn_rect, "label": lab, "action": (lambda s=st: player.spend_point(s))})
            y += btn_h + spacing

        # Single Character Sheet button (replaces Inventory + Stats buttons)
        char_sheet_btn = pygame.Rect(panel_x + panel_w - 170, panel_y + panel_h - 48, 160, 36)
        pygame.draw.rect(self.screen, (120, 100, 200), char_sheet_btn, border_radius=8)
        self._blit_text_outlined(self.screen, self.small_font, "Character (C)", char_sheet_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        # store for clicks
        self.character_sheet_open_rect = char_sheet_btn

        # Character Sheet Modal (tabbed: Equipment, Inventory, Stats)
        self.character_sheet_buttons = []
        self.inventory_cells = []
        if getattr(self, 'character_sheet_open', False) and player is not None:
            # Large modal with tabs
            modal_w, modal_h = 700, 500
            # Use stored position or default to center
            if self.character_sheet_pos is None:
                modal_x = (self.screen.get_width() - modal_w) // 2
                modal_y = (self.screen.get_height() - modal_h) // 2
                self.character_sheet_pos = (modal_x, modal_y)
            else:
                modal_x, modal_y = self.character_sheet_pos
            
            # Draw modal background
            modal_surf = pygame.Surface((modal_w, modal_h))
            modal_surf.fill((30, 30, 40))
            self.screen.blit(modal_surf, (modal_x, modal_y))
            
            # Title bar (draggable area)
            title_bar_height = 45
            self.character_sheet_title_bar = pygame.Rect(modal_x, modal_y, modal_w, title_bar_height)
            pygame.draw.rect(self.screen, (40, 40, 60), self.character_sheet_title_bar)
            
            # Title
            self._blit_text_outlined(self.screen, self.title_font, "Character Sheet [Drag to Move]", (modal_x + 20, modal_y + 12), fg=(255,255,255), outline=(0,0,0), outline_width=2)
            
            # Close button
            close_rect = pygame.Rect(modal_x + modal_w - 90, modal_y + 10, 80, 30)
            pygame.draw.rect(self.screen, (180, 80, 80), close_rect, border_radius=6)
            ct = self.small_font.render('Close', True, (0, 0, 0))
            self.screen.blit(ct, ct.get_rect(center=close_rect.center))
            self.character_sheet_buttons.append({'rect': close_rect, 'action': (lambda: setattr(self, 'character_sheet_open', False))})
            
            # Tab buttons
            tab_y = modal_y + 50
            tab_w = 120
            tab_h = 35
            tab_spacing = 10
            tabs = [('equipment', 'Equipment'), ('inventory', 'Inventory'), ('stats', 'Stats')]
            
            for idx, (tab_id, tab_label) in enumerate(tabs):
                tab_x = modal_x + 20 + idx * (tab_w + tab_spacing)
                tab_rect = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
                
                if self.character_sheet_tab == tab_id:
                    pygame.draw.rect(self.screen, (100, 80, 180), tab_rect, border_radius=6)
                    pygame.draw.rect(self.screen, (160, 140, 220), tab_rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(self.screen, (60, 60, 80), tab_rect, border_radius=6)
                
                tab_text = self.small_font.render(tab_label, True, (255, 255, 255))
                self.screen.blit(tab_text, tab_text.get_rect(center=tab_rect.center))
                self.character_sheet_buttons.append({'rect': tab_rect, 'action': (lambda t=tab_id: setattr(self, 'character_sheet_tab', t))})
            
            # Content area
            content_y = tab_y + tab_h + 15
            content_h = modal_h - (content_y - modal_y) - 20
            
            # Draw tab content
            if self.character_sheet_tab == 'equipment':
                self._draw_equipment_tab(player, modal_x, content_y, modal_w, content_h)
            elif self.character_sheet_tab == 'inventory':
                self._draw_inventory_tab(player, battle, modal_x, content_y, modal_w, content_h)
            elif self.character_sheet_tab == 'stats':
                self._draw_stats_tab(player, modal_x, content_y, modal_w, content_h)

        # Draw floating damage texts (above all UI so they're visible)
        try:
            for f in list(self.floats):
                # create text surface
                txt = f.get('text', '')
                color = f.get('color', (255, 180, 100))
                alpha = int(f.get('alpha', 255))
                # render into a surface so we can apply alpha
                surf = self.title_font.render(txt, True, color)
                # outline: draw onto temporary surface
                tw, th = surf.get_size()
                tmp = pygame.Surface((tw + 6, th + 6), pygame.SRCALPHA)
                # outline using blit of outline-colored renders (reuse small offset drawing)
                outline_color = (0, 0, 0)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        o = self.title_font.render(txt, True, outline_color)
                        tmp.blit(o, (dx + 3, dy + 3))
                tmp.blit(surf, (3, 3))
                # apply alpha
                tmp.set_alpha(alpha)
                pos = (int(f['pos'][0] - tmp.get_width() // 2), int(f['pos'][1] - tmp.get_height() // 2))
                self.screen.blit(tmp, pos)
        except Exception:
            pass
    
    def _draw_equipment_tab(self, player, modal_x, content_y, modal_w, content_h):
        """Draw equipped items with visual display"""
        equip_x = modal_x + 30
        equip_y = content_y + 10
        
        equipment_slots = [
            ('weapon', 'Weapon'),
            ('armor', 'Armor'),
            ('offhand', 'Offhand'),
            ('relic1', 'Relic 1'),
            ('relic2', 'Relic 2'),
            ('relic3', 'Relic 3')
        ]
        
        for idx, (slot_key, slot_label) in enumerate(equipment_slots):
            row = idx // 2
            col = idx % 2
            slot_x = equip_x + col * 320
            slot_y = equip_y + row * 110
            
            # Slot background
            slot_rect = pygame.Rect(slot_x, slot_y, 300, 100)
            pygame.draw.rect(self.screen, (50, 50, 70), slot_rect, border_radius=8)
            
            # Slot label
            self._blit_text_outlined(self.screen, self.small_font, slot_label, (slot_x + 10, slot_y + 8), fg=(180,180,200), outline=(0,0,0), outline_width=1)
            
            item_id = player.equipment.get(slot_key)
            if item_id:
                # Load item data
                item_data = self.shop_loader.find_item(item_id) if getattr(self, 'shop_loader', None) else None
                item_name = item_data.get('name') if item_data else item_id
                
                # Item icon
                icon_rect = pygame.Rect(slot_x + 15, slot_y + 30, 55, 55)
                if self.assets_path and item_data:
                    icon_path = self.assets_path / 'images' / 'items' / f"{item_id}.png"
                    if icon_path.exists():
                        ico = pygame.image.load(str(icon_path)).convert_alpha()
                        ico = pygame.transform.smoothscale(ico, (55, 55))
                        self.screen.blit(ico, icon_rect)
                    else:
                        pygame.draw.rect(self.screen, (100, 100, 140), icon_rect, border_radius=6)
                else:
                    pygame.draw.rect(self.screen, (100, 100, 140), icon_rect, border_radius=6)
                
                # Item name and stats
                name_y = slot_y + 35
                self._blit_text_outlined(self.screen, self.small_font, item_name[:20], (slot_x + 80, name_y), fg=(220,220,220), outline=(0,0,0), outline_width=1)
                
                # Show key stats
                stats_text = []
                if item_data:
                    if item_data.get('attack'): stats_text.append(f"+{item_data['attack']} ATK")
                    if item_data.get('defense'): stats_text.append(f"+{item_data['defense']} DEF")
                    if item_data.get('penetration'): stats_text.append(f"+{item_data['penetration']:.0f} PEN")
                    if item_data.get('max_hp'): stats_text.append(f"+{item_data['max_hp']} HP")
                
                for i, stat in enumerate(stats_text[:2]):  # Show max 2 stats
                    self._blit_text_outlined(self.screen, self.small_font, stat, (slot_x + 80, name_y + 20 + i * 18), fg=(180,220,180), outline=(0,0,0), outline_width=1)
                
                # Unequip button
                unequip_rect = pygame.Rect(slot_x + 210, slot_y + 60, 80, 30)
                pygame.draw.rect(self.screen, (180, 80, 80), unequip_rect, border_radius=6)
                unequip_text = self.small_font.render("Unequip", True, (0, 0, 0))
                self.screen.blit(unequip_text, unequip_text.get_rect(center=unequip_rect.center))
                self.character_sheet_buttons.append({'rect': unequip_rect, 'action': (lambda p=player, s=slot_key: p.unequip(s))})
            else:
                # Empty slot
                empty_rect = pygame.Rect(slot_x + 15, slot_y + 30, 55, 55)
                pygame.draw.rect(self.screen, (40, 40, 60), empty_rect, border_radius=6)
                self._blit_text_outlined(self.screen, self.small_font, "Empty", (slot_x + 80, slot_y + 50), fg=(120,120,120), outline=(0,0,0), outline_width=1)
    
    def _draw_inventory_tab(self, player, battle, modal_x, content_y, modal_w, content_h):
        """Draw inventory grid with pagination"""
        items = list(player.inventory.items())
        items_per_page = 18  # 3 rows x 6 cols
        total_pages = max(1, (len(items) + items_per_page - 1) // items_per_page)
        page = getattr(self, 'inventory_page', 0)
        
        # Pagination controls
        if page > 0:
            prev_rect = pygame.Rect(modal_x + 30, content_y + content_h - 40, 80, 30)
            pygame.draw.rect(self.screen, (80, 100, 180), prev_rect, border_radius=6)
            prev_text = self.small_font.render("< Prev", True, (255, 255, 255))
            self.screen.blit(prev_text, prev_text.get_rect(center=prev_rect.center))
            self.character_sheet_buttons.append({'rect': prev_rect, 'action': (lambda: setattr(self, 'inventory_page', max(0, page - 1)))})
        
        if page < total_pages - 1:
            next_rect = pygame.Rect(modal_x + modal_w - 110, content_y + content_h - 40, 80, 30)
            pygame.draw.rect(self.screen, (80, 100, 180), next_rect, border_radius=6)
            next_text = self.small_font.render("Next >", True, (255, 255, 255))
            self.screen.blit(next_text, next_text.get_rect(center=next_rect.center))
            self.character_sheet_buttons.append({'rect': next_rect, 'action': (lambda: setattr(self, 'inventory_page', min(total_pages - 1, page + 1)))})
        
        # Page indicator
        page_text = self.small_font.render(f"Page {page + 1}/{total_pages}", True, (200, 200, 200))
        self.screen.blit(page_text, (modal_x + modal_w // 2 - 30, content_y + content_h - 32))
        
        # Grid
        cols = 6
        cell_w = 90
        cell_h = 90
        pad = 10
        start_x = modal_x + 30
        start_y = content_y + 10
        
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        page_items = items[start_idx:end_idx]
        
        for idx, (iid, cnt) in enumerate(page_items):
            cx = start_x + (idx % cols) * (cell_w + pad)
            cy = start_y + (idx // cols) * (cell_h + pad)
            rect = pygame.Rect(cx, cy, cell_w, cell_h)
            pygame.draw.rect(self.screen, (60, 60, 90), rect, border_radius=6)
            
            if self.inventory_selected == iid:
                pygame.draw.rect(self.screen, (140, 120, 60), rect, width=3, border_radius=6)
            
            # Load item data
            item_def = self.shop_loader.find_item(iid) if getattr(self, 'shop_loader', None) else None
            name = item_def.get('name') if item_def else iid
            
            # Icon
            ico_rect = pygame.Rect(cx + 8, cy + 8, cell_w - 16, cell_h - 30)
            if self.assets_path and item_def:
                icon_path = self.assets_path / 'images' / 'items' / f"{iid}.png"
                if icon_path.exists():
                    ico = pygame.image.load(str(icon_path)).convert_alpha()
                    ico = pygame.transform.smoothscale(ico, (ico_rect.w, ico_rect.h))
                    self.screen.blit(ico, ico_rect)
                else:
                    pygame.draw.rect(self.screen, (100, 100, 140), ico_rect, border_radius=4)
            else:
                pygame.draw.rect(self.screen, (100, 100, 140), ico_rect, border_radius=4)
            
            # Count badge
            badge_rect = pygame.Rect(cx + cell_w - 24, cy + 6, 18, 14)
            pygame.draw.rect(self.screen, (10, 10, 10), badge_rect, border_radius=3)
            self._blit_text_outlined(self.screen, self.small_font, str(cnt), badge_rect.center, fg=(255,255,255), outline=(0,0,0), outline_width=1, center=True)
            
            # Item name at bottom of cell, scaled to fit
            if name:
                name_text = name[:15]  # Truncate if too long
                # Calculate font size to fit within cell width
                max_width = cell_w - 8
                test_surf = self.small_font.render(name_text, True, (255, 255, 255))
                
                # If text is too wide, try progressively smaller text or truncate
                if test_surf.get_width() > max_width:
                    # Truncate with ellipsis
                    while name_text and self.small_font.render(name_text + '...', True, (255, 255, 255)).get_width() > max_width:
                        name_text = name_text[:-1]
                    if name_text:
                        name_text = name_text + '...'
                
                # Draw name at bottom of cell
                name_y = cy + cell_h - 18
                self._blit_text_outlined(self.screen, self.small_font, name_text, (cx + 4, name_y), fg=(200,200,200), outline=(0,0,0), outline_width=1)
            
            # Register for clicks
            self.inventory_cells.append({'rect': rect, 'item_id': iid, 'count': cnt, 'def': item_def})
        
        # Selected item details
        if self.inventory_selected:
            sel = None
            for c in self.inventory_cells:
                if c['item_id'] == self.inventory_selected:
                    sel = c
                    break
            
            if sel:
                detail_y = start_y + 3 * (cell_h + pad) + 20
                detail_rect = pygame.Rect(modal_x + 30, detail_y, modal_w - 60, 80)
                pygame.draw.rect(self.screen, (40, 40, 60), detail_rect, border_radius=6)
                
                # Description
                desc = sel['def'].get('description', 'No description') if sel.get('def') else 'No description'
                self._blit_text_outlined(self.screen, self.small_font, desc[:80], (detail_rect.x + 10, detail_rect.y + 10), fg=(200,200,200), outline=(0,0,0), outline_width=1)
                
                # Action buttons
                btn_y = detail_rect.y + 45
                if sel.get('def') and sel['def'].get('type') in ('weapon', 'armor', 'offhand', 'relic'):
                    equip_rect = pygame.Rect(detail_rect.x + detail_rect.w - 110, btn_y, 100, 30)
                    pygame.draw.rect(self.screen, (100, 180, 100), equip_rect, border_radius=6)
                    equip_text = self.small_font.render('Equip', True, (0, 0, 0))
                    self.screen.blit(equip_text, equip_text.get_rect(center=equip_rect.center))
                    def make_equip(iid=sel['item_id']):
                        def act():
                            if player.equip_item_by_id(iid):
                                player.remove_item(iid, 1)
                                self.inventory_selected = None
                        return act
                    self.character_sheet_buttons.append({'rect': equip_rect, 'action': make_equip()})
                elif sel.get('def') and sel['def'].get('type') == 'consumable':
                    use_rect = pygame.Rect(detail_rect.x + detail_rect.w - 110, btn_y, 100, 30)
                    pygame.draw.rect(self.screen, (180, 140, 60), use_rect, border_radius=6)
                    use_text = self.small_font.render('Use', True, (0, 0, 0))
                    self.screen.blit(use_text, use_text.get_rect(center=use_rect.center))
                    def make_use(iid=sel['item_id'], idef=sel.get('def')):
                        def act():
                            eff = idef.get('effect', {}) if idef else {}
                            if eff.get('heal'):
                                player.hp = min(player.max_hp, player.hp + eff.get('heal'))
                            if player.remove_item(iid, 1):
                                if getattr(battle, 'turn', None) == 'player':
                                    battle.turn = 'enemy'
                                    battle.last_action_time = pygame.time.get_ticks() / 1000.0
                                self.inventory_selected = None
                        return act
                    self.character_sheet_buttons.append({'rect': use_rect, 'action': make_use()})
    
    def _draw_stats_tab(self, player, modal_x, content_y, modal_w, content_h):
        """Draw player stats with pagination"""
        def_pct = player.get_effective_defense_percent() if hasattr(player, 'get_effective_defense_percent') else 0
        pen_pct = player.get_effective_penetration_percent() if hasattr(player, 'get_effective_penetration_percent') else 0
        
        # Calculate next level XP requirement
        next_level_xp = int((player.level ** 1.5) * 100)
        
        # All stat lines (can be extended easily)
        all_stat_lines = [
            ("Basic Info", None),
            (f"  Name: {getattr(player, 'name', 'Player')}", None),
            (f"  Level: {getattr(player, 'level', 1)}", None),
            (f"  XP: {getattr(player, 'xp', 0)} / {next_level_xp}", None),
            (f"  Gold: {player.gold}g", (255, 215, 0)),
            ("", None),
            ("Combat Stats", None),
            (f"  HP: {player.hp} / {player.max_hp}", (100, 255, 100)),
            (f"  Attack: {player.atk}", (255, 150, 100)),
            (f"  Defense: {player.defense} ({def_pct:.1f}% reduction)", (150, 200, 255)),
            (f"  Penetration: {getattr(player, 'penetration', 0):.1f} ({pen_pct:.1f}%)", (255, 180, 255)),
            ("", None),
            ("Critical Stats", None),
            (f"  Crit Chance: {int(getattr(player, 'critchance', 0.0) * 100)}%", (255, 100, 100)),
            (f"  Crit Damage: {round(getattr(player, 'critdamage', 1.5), 2)}x", (255, 100, 100)),
            ("", None),
            ("Agility Stats", None),
            (f"  Agility: {getattr(player, 'agility', 0)}", (100, 255, 200)),
            (f"  Dodge Chance: {getattr(player, 'dodge_chance', 0.0) * 100:.1f}%", (100, 255, 200)),
            ("", None),
            ("Challenge Progress", None),
            (f"  Challenge Coins: {getattr(player, 'challenge_coins', 0)}", (255, 200, 100)),
            (f"  Highest Wave: {getattr(player, 'highest_wave', 0)}", (200, 200, 255)),
        ]
        
        # Pagination setup
        lines_per_page = 14  # Number of stat lines per page
        total_pages = max(1, (len(all_stat_lines) + lines_per_page - 1) // lines_per_page)
        page = getattr(self, 'stats_page', 0)
        
        # Ensure page is within bounds
        if page >= total_pages:
            page = total_pages - 1
            self.stats_page = page
        if page < 0:
            page = 0
            self.stats_page = page
        
        # Get current page lines
        start_idx = page * lines_per_page
        end_idx = min(start_idx + lines_per_page, len(all_stat_lines))
        page_lines = all_stat_lines[start_idx:end_idx]
        
        # Draw stats
        stats_x = modal_x + 40
        stats_y = content_y + 20
        
        y_offset = 0
        for line, color in page_lines:
            if line == "":
                y_offset += 10
                continue
            
            if line.startswith("  "):
                # Indented stat
                fg_color = color if color else (220, 220, 220)
            else:
                # Section header
                fg_color = (255, 220, 100)
            
            self._blit_text_outlined(self.screen, self.small_font, line, (stats_x, stats_y + y_offset), fg=fg_color, outline=(0,0,0), outline_width=1)
            y_offset += 24
        
        # Pagination controls
        if total_pages > 1:
            btn_y = content_y + content_h - 40
            
            if page > 0:
                prev_rect = pygame.Rect(modal_x + 30, btn_y, 80, 30)
                pygame.draw.rect(self.screen, (80, 100, 180), prev_rect, border_radius=6)
                prev_text = self.small_font.render("< Prev", True, (255, 255, 255))
                self.screen.blit(prev_text, prev_text.get_rect(center=prev_rect.center))
                self.character_sheet_buttons.append({'rect': prev_rect, 'action': (lambda: setattr(self, 'stats_page', max(0, page - 1)))})
            
            if page < total_pages - 1:
                next_rect = pygame.Rect(modal_x + modal_w - 110, btn_y, 80, 30)
                pygame.draw.rect(self.screen, (80, 100, 180), next_rect, border_radius=6)
                next_text = self.small_font.render("Next >", True, (255, 255, 255))
                self.screen.blit(next_text, next_text.get_rect(center=next_rect.center))
                self.character_sheet_buttons.append({'rect': next_rect, 'action': (lambda: setattr(self, 'stats_page', min(total_pages - 1, page + 1)))})
            
            # Page indicator
            page_text = self.small_font.render(f"Page {page + 1}/{total_pages}", True, (200, 200, 200))
            self.screen.blit(page_text, (modal_x + modal_w // 2 - 30, btn_y + 5))