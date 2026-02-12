# src/ui_manager.py
import pygame
import time
try:
    # when running as top-level script
    from shop import Shop
except Exception:
    # when running as package (e.g., src.ui_manager)
    from .shop import Shop


class UIManager:
    # Rarity color definitions
    RARITY_COLORS = {
        'common': (255, 255, 255),  # white
        'uncommon': (30, 255, 0),  # green
        'rare': (70, 130, 255),  # blue
        'epic': (163, 53, 238),  # purple
        'legendary': (255, 165, 0),  # gold
        'mythical': (255, 40, 40),  # red
        'ancient': (0, 0, 0),  # black (with white outline)
    }
    
    @staticmethod
    def get_rarity_color(rarity):
        """Get color tuple for item rarity"""
        return UIManager.RARITY_COLORS.get(rarity, UIManager.RARITY_COLORS['common'])
    
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
        self.inventory_filter = 'all'
        self.stats_page = 0
        self.character_sheet_open_rect = None
        # Skills UI modal
        self.skills_ui_open = False
        self.skills_ui_buttons = []
        self.skills_page = 0
        self.skills_scroll = 0  # Scroll offset for skills
        self.skills_ui_rect = None
        # Crafting UI modal
        self.crafting_ui_open = False
        self.crafting_ui_buttons = []
        self.crafting_selected_recipe = None
        self.crafting_ui_rect = None
        # Combat Log UI
        self.combat_log_open = True  # Start open by default
        self.combat_log_dragging = False
        self.combat_log_drag_offset = (0, 0)
        self.combat_log_pos = None  # Will be (x, y) when set, default to right side
        self.combat_log_scroll = 0  # Scroll offset for log
        # Dragging state for moveable character sheet
        self.character_sheet_dragging = False
        self.character_sheet_drag_offset = (0, 0)
        self.character_sheet_pos = None  # Will be (x, y) when set
        # Floating damage texts: list of dicts {text, pos, start_time, duration, color, alpha, dy}
        self.floats = []
        # Enemy images cache: {enemy_id: pygame.Surface}
        self.enemy_images = {}
        self.current_enemy_image = None
        # Player character image
        self.player_image = None
        try:
            if self.assets_path:
                player_path = self.assets_path / "images" / "characters" / "mage.png"
                if player_path.exists():
                    loaded_img = pygame.image.load(str(player_path)).convert_alpha()
                    # Scale to reasonable size (max 200x200 for player)
                    orig_w, orig_h = loaded_img.get_size()
                    max_size = 200
                    if orig_w > max_size or orig_h > max_size:
                        scale = min(max_size / orig_w, max_size / orig_h)
                        new_w = int(orig_w * scale)
                        new_h = int(orig_h * scale)
                        loaded_img = pygame.transform.smoothscale(loaded_img, (new_w, new_h))
                    self.player_image = loaded_img
        except Exception:
            self.player_image = None

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
            {
                "rect": pygame.Rect(screen_width - 520, screen_height - 100, 200, 60),
                "label": "Block",
                "action": battle.player_block,
            },
        ]
        # Store battle reference for skill buttons
        self.battle = battle

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
        
        # Toggle skills UI with 'K' key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
            self.skills_ui_open = not self.skills_ui_open
            return
        
        # Toggle crafting UI with 'R' key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.crafting_ui_open = not self.crafting_ui_open
            return
        
        # Toggle combat log with 'L' key
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            self.combat_log_open = not self.combat_log_open
            return
        
        # Skill hotkeys (1-5)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self._use_skill_slot(0)
                return
            elif event.key == pygame.K_2:
                self._use_skill_slot(1)
                return
            elif event.key == pygame.K_3:
                self._use_skill_slot(2)
                return
            elif event.key == pygame.K_4:
                self._use_skill_slot(3)
                return
            elif event.key == pygame.K_5:
                self._use_skill_slot(4)
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check skill buttons
            for btn in getattr(self, 'skill_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return
            
            # Check character sheet buttons first (close, tabs, etc.) before dragging
            for btn in getattr(self, 'character_sheet_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return
            
            # Check if dragging combat log title bar
            if getattr(self, 'combat_log_open', False) and hasattr(self, 'combat_log_title_bar'):
                if self.combat_log_title_bar.collidepoint(event.pos):
                    self.combat_log_dragging = True
                    pos = self.combat_log_pos or (self.screen.get_width() - 320, 80)
                    self.combat_log_drag_offset = (event.pos[0] - pos[0], event.pos[1] - pos[1])
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
            
            # skills UI open/close button
            if getattr(self, 'skills_ui_rect', None) and self.skills_ui_rect.collidepoint(event.pos):
                self.skills_ui_open = not self.skills_ui_open
                return
            
            # crafting UI open/close button
            if getattr(self, 'crafting_ui_rect', None) and self.crafting_ui_rect.collidepoint(event.pos):
                self.crafting_ui_open = not self.crafting_ui_open
                return
            
            # combat log toggle button
            if getattr(self, 'combat_log_toggle_rect', None) and self.combat_log_toggle_rect.collidepoint(event.pos):
                self.combat_log_open = not self.combat_log_open
                return
            
            # skills UI modal buttons
            for btn in getattr(self, 'skills_ui_buttons', []):
                if btn['rect'].collidepoint(event.pos):
                    btn['action']()
                    return
            
            # crafting UI modal buttons
            for btn in getattr(self, 'crafting_ui_buttons', []):
                if btn['rect'].collidepoint(event.pos):
                    btn['action']()
                    return
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.character_sheet_dragging = False
            self.combat_log_dragging = False
        
        if event.type == pygame.MOUSEMOTION:
            if getattr(self, 'combat_log_dragging', False):
                new_x = event.pos[0] - self.combat_log_drag_offset[0]
                new_y = event.pos[1] - self.combat_log_drag_offset[1]
                # Clamp to screen bounds
                new_x = max(0, min(new_x, self.screen.get_width() - 300))
                new_y = max(0, min(new_y, self.screen.get_height() - 400))
                self.combat_log_pos = (new_x, new_y)
            
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
                    is_heal = ev.get('is_heal', False)
                    
                    if is_heal:
                        # Healing counter (green)
                        text = f"+{ev.get('amount', 0)}"
                        color = (100, 255, 100)
                    else:
                        # Damage counter
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
                        # player damage/healing near player area (center-left, vertically centered)
                        pos = (screen_w // 2 - 100, screen_h // 2)

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
        
        # Load enemy image if battle enemy has changed
        if battle and hasattr(battle, 'enemy') and battle.enemy:
            enemy = battle.enemy
            enemy_id = getattr(enemy, 'id', None)
            image_filename = getattr(enemy, 'image', None)
            
            # Load image if we have a filename and haven't loaded it yet
            if image_filename and enemy_id:
                if enemy_id not in self.enemy_images:
                    try:
                        if self.assets_path:
                            image_path = self.assets_path / "images" / "monsters" / image_filename
                            if image_path.exists():
                                loaded_img = pygame.image.load(str(image_path)).convert_alpha()
                                # Scale to a smaller size (max 200x200 for enemy)
                                orig_w, orig_h = loaded_img.get_size()
                                max_size = 200
                                if orig_w > max_size or orig_h > max_size:
                                    scale = min(max_size / orig_w, max_size / orig_h)
                                    new_w = int(orig_w * scale)
                                    new_h = int(orig_h * scale)
                                    loaded_img = pygame.transform.smoothscale(loaded_img, (new_w, new_h))
                                self.enemy_images[enemy_id] = loaded_img
                            else:
                                self.enemy_images[enemy_id] = None  # Mark as not found
                    except Exception:
                        self.enemy_images[enemy_id] = None
                
                # Set current image to display
                self.current_enemy_image = self.enemy_images.get(enemy_id)
            else:
                self.current_enemy_image = None
        else:
            self.current_enemy_image = None
        
        return

    def draw(self, player=None, battle=None):
        # Draw a background panel for UI (image if available, otherwise a semi-transparent rect)
        screen_w, screen_h = self.screen.get_size()
        # larger panel to avoid content overlap - extend to bottom of screen
        panel_w = 520  # Increased to fit equipment display with Unequip buttons
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
        
        # Draw equipped skill buttons (1-5 keys)
        if player is not None and hasattr(player, 'equipped_skills'):
            equipped = player.equipped_skills[:5]  # Max 5 skills
            skill_btn_w, skill_btn_h = 80, 40
            skill_start_x = screen_w - 740
            skill_y = screen_h - 100
            
            for i, skill_id in enumerate(equipped):
                skill_x = skill_start_x + i * (skill_btn_w + 10)
                skill_rect = pygame.Rect(skill_x, skill_y, skill_btn_w, skill_btn_h)
                
                # Check if skill is usable (has mana, no cooldown)
                can_use = True
                skill_data = None
                skill_level = 1
                if hasattr(battle, 'skill_manager'):
                    skill_data = battle.skill_manager.get_skill(skill_id)
                    skill_level = getattr(player, 'skill_levels', {}).get(skill_id, 1)
                    if skill_data:
                        base_mana_cost = skill_data.get('mana_cost', 0)
                        actual_mana_cost = int(base_mana_cost * (1 + (skill_level - 1) * 0.2))
                        if player.current_mana < actual_mana_cost:
                            can_use = False
                
                # Color based on usability
                btn_color = (50, 150, 200) if can_use else (80, 80, 80)
                pygame.draw.rect(self.screen, btn_color, skill_rect, border_radius=6)
                pygame.draw.rect(self.screen, (255, 255, 255), skill_rect, 2, border_radius=6)
                
                # Skill name (shortened)
                skill_name = skill_id.replace('skill_', '').replace('_', ' ')[:8]
                text_color = (255, 255, 255) if can_use else (120, 120, 120)
                skill_text = pygame.font.Font(None, 18).render(skill_name, True, text_color)
                self.screen.blit(skill_text, skill_text.get_rect(center=(skill_x + skill_btn_w//2, skill_y + 12)))
                
                # Skill level indicator
                if skill_level > 1:
                    level_badge = pygame.font.Font(None, 14).render(f"Lv{skill_level}", True, (255, 255, 100))
                    self.screen.blit(level_badge, (skill_x + skill_btn_w - 22, skill_y + 3))
                
                # Key hint
                key_hint = pygame.font.Font(None, 16).render(f"[{i+1}]", True, (200, 200, 100))
                self.screen.blit(key_hint, (skill_x + 5, skill_y + skill_btn_h - 16))
                
                # Store for click handling
                if not hasattr(self, 'skill_buttons'):
                    self.skill_buttons = []
                
                def make_use_skill(sid=skill_id):
                    def action():
                        if hasattr(battle, 'player_use_skill'):
                            battle.player_use_skill(sid)
                    return action
                
                # Add to buttons for click handling (store separately to avoid conflicts)
                if i >= len(getattr(self, 'skill_buttons', [])):
                    self.skill_buttons.append({'rect': skill_rect, 'action': make_use_skill()})
                else:
                    self.skill_buttons[i] = {'rect': skill_rect, 'action': make_use_skill()}

        # Affichage des infos joueur / ennemi
        x = panel_x + 12
        y = panel_y + 12
        line_h = 28

        if player is not None:
            # Player HP bar (draw bar first, then text)
            bar_x, bar_y = x + 150, y
            bar_width, bar_height = 200, 20
            pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
            hp_ratio = player.hp / max(1, player.max_hp)
            filled_width = int(bar_width * hp_ratio)
            hp_color = (100, 255, 100) if hp_ratio > 0.5 else (255, 200, 100) if hp_ratio > 0.25 else (255, 100, 100)
            if filled_width > 0:
                pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, filled_width, bar_height), border_radius=4)
            pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=4)
            
            # Draw text AFTER bar so it appears on top
            self._blit_text_outlined(self.screen, self.small_font, f"Player HP: {player.hp}/{player.max_hp}", (x, y), fg=(255,255,255), outline=(0,0,0), outline_width=2)
            
            y += line_h
            
            # Player Mana bar
            current_mana = getattr(player, 'current_mana', 0)
            max_mana = getattr(player, 'max_mana', 0)
            if max_mana > 0:
                # Mana bar (draw bar first, then text)
                mana_bar_y = y
                pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, mana_bar_y, bar_width, bar_height), border_radius=4)
                mana_ratio = current_mana / max(1, max_mana)
                mana_filled = int(bar_width * mana_ratio)
                if mana_filled > 0:
                    pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, mana_bar_y, mana_filled, bar_height), border_radius=4)
                pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, mana_bar_y, bar_width, bar_height), 2, border_radius=4)
                
                # Draw text AFTER bar
                self._blit_text_outlined(self.screen, self.small_font, f"Mana: {current_mana}/{max_mana}", (x, y), fg=(150,200,255), outline=(0,0,0), outline_width=2)
                if mana_filled > 0:
                    pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, mana_bar_y, mana_filled, bar_height), border_radius=4)
                pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, mana_bar_y, bar_width, bar_height), 2, border_radius=4)
                
                y += line_h

        if battle is not None and getattr(battle, "enemy", None):
            enemy = battle.enemy
            self._blit_text_outlined(self.screen, self.small_font, f"Enemy: {getattr(enemy, 'name', 'Unknown')}", (x, y), fg=(255,200,200), outline=(0,0,0), outline_width=2)
            y += line_h

            # Enemy HP bar is now drawn near the enemy sprite, not here
            y += line_h

        # Stats joueur (gold, level)
        if player is not None:
            gold = getattr(player, "gold", 0)
            self._blit_text_outlined(self.screen, self.small_font, f"Gold: {gold}", (x, y), fg=(255,215,0), outline=(0,0,0), outline_width=2)
            y += line_h

            level = getattr(player, "level", 1)
            self._blit_text_outlined(self.screen, self.small_font, f"Level: {level}", (x, y), fg=(200,200,255), outline=(0,0,0), outline_width=2)
            y += line_h
            
            # XP counter with current/required display
            current_xp = getattr(player, "xp", 0)
            xp_required = int((level ** 1.5) * 100)
            self._blit_text_outlined(self.screen, self.small_font, f"XP: {current_xp}/{xp_required}", (x, y), fg=(100,255,100), outline=(0,0,0), outline_width=2)
            y += line_h

            # Compact stats block (two columns)
            stats = [
                ("ATK", getattr(player, "atk", 0)),
                ("DEF", getattr(player, "defense", 0)),
                ("PEN", f"{getattr(player, 'penetration', 0):.1f}"),
                ("M.PEN", f"{getattr(player, 'magic_penetration', 0):.1f}"),
                ("MAG", getattr(player, "magic_power", 0)),
                ("CRIT%", f"{getattr(player, 'critchance', 0.0) * 100:.0f}"),
                ("CRITx", f"{getattr(player, 'critdamage', 1.5):.2f}"),
                ("AGI", getattr(player, "agility", 0)),
                ("DODGE%", f"{getattr(player, 'dodge_chance', 0.0) * 100:.1f}"),
                ("LIFESTEAL%", f"{getattr(player, 'lifesteal', 0.0):.1f}"),
                ("HP REGEN", f"{getattr(player, 'hp_regen', 0.0):.1f}"),
                ("MANA REGEN", f"{getattr(player, 'mana_regen', 0)}"),
            ]

            col_w = 160
            row_h = 20
            for i, (label, value) in enumerate(stats):
                col = i % 2
                row = i // 2
                stat_x = x + (col * col_w)
                stat_y = y + (row * row_h)
                self._blit_text_outlined(
                    self.screen,
                    self.small_font,
                    f"{label}: {value}",
                    (stat_x, stat_y),
                    fg=(210, 210, 210),
                    outline=(0, 0, 0),
                    outline_width=2,
                )

            y += row_h * ((len(stats) + 1) // 2)

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
            
            # Truncate item name if too long to prevent overlap
            max_name_length = 18
            if len(item_name) > max_name_length:
                item_name = item_name[:max_name_length-2] + ".."
            
            # Slot name and item
            slot_text = f"{slot_label}: {item_name}"
            self._blit_text_outlined(self.screen, self.small_font, slot_text, (x, y), fg=(220,220,220), outline=(0,0,0), outline_width=2)
            
            # Unequip button (only if something is equipped)
            if item_id:
                unequip_rect = pygame.Rect(x + 280, y - 4, 80, 24)
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

            labels = [("+ATK", "atk"), ("+DEF", "def"), ("+HP", "hp"), ("+AGI", "agi"), ("+MAG", "mag")]
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

        # Draw enemy image and HP bar BEFORE modals (so modals appear on top)
        screen_w, screen_h = self.screen.get_size()
        if battle and getattr(battle, "enemy", None):
            enemy = battle.enemy
            
            # Calculate positions for enemy sprite and HP bar
            if self.current_enemy_image:
                # Position at top-center of screen
                enemy_img_x = screen_w // 2 - self.current_enemy_image.get_width() // 2
                enemy_img_y = 60  # Top of screen with some padding
                
                # Draw a semi-transparent black backdrop
                backdrop_padding = 15
                backdrop = pygame.Surface((self.current_enemy_image.get_width() + backdrop_padding * 2, 
                                          self.current_enemy_image.get_height() + backdrop_padding * 2), pygame.SRCALPHA)
                backdrop.fill((0, 0, 0, 120))
                self.screen.blit(backdrop, (enemy_img_x - backdrop_padding, enemy_img_y - backdrop_padding))
                
                # Draw the enemy image
                self.screen.blit(self.current_enemy_image, (enemy_img_x, enemy_img_y))
                
                # HP bar below the sprite
                bar_y = enemy_img_y + self.current_enemy_image.get_height() + 10
            else:
                # No sprite, so position HP bar at top-center
                bar_y = 80
            
            # Draw enemy HP bar (always visible if there's an enemy)
            bar_width, bar_height = 180, 16
            bar_x = screen_w // 2 - bar_width // 2
            hp_ratio = (enemy.hp / enemy.max_hp) if getattr(enemy, "max_hp", 1) > 0 else 0
            
            # HP bar background
            pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
            # HP bar fill
            pygame.draw.rect(self.screen, (50, 220, 50), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height), border_radius=3)
            # HP bar border
            pygame.draw.rect(self.screen, (180, 180, 180), (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=3)
            # HP text centered on bar
            hp_text = f"{enemy.hp}/{enemy.max_hp}"
            self._blit_text_outlined(self.screen, self.small_font, hp_text, (bar_x + bar_width // 2, bar_y + bar_height // 2), fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)

        # UI buttons arranged in two rows to prevent overlapping
        btn_w = 150
        btn_h = 34
        btn_spacing = 8
        
        # Top row buttons (right side)
        top_row_y = panel_y + panel_h - 80
        
        # Character Sheet button (top right)
        char_sheet_btn = pygame.Rect(panel_x + panel_w - btn_w - 10, top_row_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (120, 100, 200), char_sheet_btn, border_radius=8)
        self._blit_text_outlined(self.screen, self.small_font, "Character (C)", char_sheet_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        self.character_sheet_open_rect = char_sheet_btn
        
        # Skills button (top middle-right)
        skills_btn = pygame.Rect(panel_x + panel_w - (btn_w * 2) - btn_spacing - 10, top_row_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (200, 120, 100), skills_btn, border_radius=8)
        self._blit_text_outlined(self.screen, self.small_font, "Skills (K)", skills_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        self.skills_ui_rect = skills_btn
        
        # Bottom row buttons
        bottom_row_y = panel_y + panel_h - 40
        
        # Combat Log toggle button (bottom left)
        log_btn = pygame.Rect(panel_x + 10, bottom_row_y, btn_w, btn_h)
        log_color = (100, 200, 120) if self.combat_log_open else (80, 80, 80)
        pygame.draw.rect(self.screen, log_color, log_btn, border_radius=8)
        self._blit_text_outlined(self.screen, self.small_font, "Log (L)", log_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        self.combat_log_toggle_rect = log_btn
        
        # Crafting button (bottom middle-left)
        crafting_btn = pygame.Rect(panel_x + btn_w + btn_spacing + 10, bottom_row_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (180, 120, 200), crafting_btn, border_radius=8)
        self._blit_text_outlined(self.screen, self.small_font, "Crafting (R)", crafting_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        self.crafting_ui_rect = crafting_btn

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

        # Skills UI Modal
        if getattr(self, 'skills_ui_open', False) and player is not None and battle is not None:
            self._draw_skills_ui(player, battle)
        
        # Crafting UI Modal
        if getattr(self, 'crafting_ui_open', False) and player is not None:
            self._draw_crafting_ui(player, battle)
        
        # Combat Log Window (draggable)
        if battle is not None:
            self._draw_combat_log(battle)
        
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
                
                # Item name and stats (use rarity color)
                name_y = slot_y + 35
                rarity = item_data.get('rarity', 'common') if item_data else 'common'
                name_color = self.get_rarity_color(rarity)
                outline_color = (255, 255, 255) if rarity == 'ancient' else (0, 0, 0)
                outline_width = 2 if rarity == 'ancient' else 1
                self._blit_text_outlined(self.screen, self.small_font, item_name[:20], (slot_x + 80, name_y), fg=name_color, outline=outline_color, outline_width=outline_width)
                
                # Show key stats
                stats_text = []
                if item_data:
                    if item_data.get('attack'): stats_text.append(f"+{item_data['attack']} ATK")
                    if item_data.get('defense'): stats_text.append(f"+{item_data['defense']} DEF")
                    if item_data.get('penetration'): stats_text.append(f"+{item_data['penetration']:.0f} PEN")
                    if item_data.get('max_hp'): stats_text.append(f"+{item_data['max_hp']} HP")
                    if item_data.get('magic_power'): stats_text.append(f"+{item_data['magic_power']} MAG")
                    if item_data.get('magic_penetration'): stats_text.append(f"+{item_data['magic_penetration']:.0f} M.PEN")
                    if item_data.get('max_mana'): stats_text.append(f"+{item_data['max_mana']} MANA")
                    if item_data.get('mana_regen'): stats_text.append(f"+{item_data['mana_regen']} M.REG")
                
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
        # Filter buttons
        filter_labels = [
            ('all', 'ALL'),
            ('weapon', 'WEAPONS'),
            ('equippable', 'EQUIPPABLE'),
            ('material', 'MATERIALS'),
            ('consumable', 'CONSUMABLES'),
            ('misc', 'MISC'),
        ]
        filter_x = modal_x + 30
        filter_y = content_y + 5
        filter_w = 90
        filter_h = 24
        filter_gap = 6

        def set_filter(key):
            self.inventory_filter = key
            self.inventory_page = 0
            self.inventory_selected = None

        for i, (key, label) in enumerate(filter_labels):
            fx = filter_x + i * (filter_w + filter_gap)
            rect = pygame.Rect(fx, filter_y, filter_w, filter_h)
            is_active = (self.inventory_filter == key)
            color = (120, 140, 200) if is_active else (60, 60, 80)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (180, 180, 220), rect, 2, border_radius=6)
            self._blit_text_outlined(
                self.screen,
                pygame.font.Font(None, 18),
                label,
                rect.center,
                fg=(255, 255, 255),
                outline=(0, 0, 0),
                outline_width=1,
                center=True,
            )
            self.character_sheet_buttons.append({'rect': rect, 'action': (lambda k=key: set_filter(k))})

        def get_item_type(item_def):
            if not item_def:
                return 'misc'
            return item_def.get('type', 'misc')

        def matches_filter(item_def):
            itype = get_item_type(item_def)
            if self.inventory_filter == 'all':
                return True
            if self.inventory_filter == 'weapon':
                return itype == 'weapon'
            if self.inventory_filter == 'equippable':
                return itype in ('weapon', 'armor', 'offhand', 'relic')
            if self.inventory_filter == 'material':
                return itype == 'material'
            if self.inventory_filter == 'consumable':
                return itype == 'consumable'
            if self.inventory_filter == 'misc':
                return itype not in ('weapon', 'armor', 'offhand', 'relic', 'material', 'consumable')
            return True

        items = []
        for iid, cnt in list(player.inventory.items()):
            item_def = self.shop_loader.find_item(iid) if getattr(self, 'shop_loader', None) else None
            if matches_filter(item_def):
                items.append((iid, cnt))
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
        start_y = content_y + 45
        
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
            
            # Icon - check if item has an image field
            ico_rect = pygame.Rect(cx + 8, cy + 8, cell_w - 16, cell_h - 30)
            image_filename = item_def.get('image') if item_def else None
            
            if image_filename and self.assets_path:
                # Try to load custom item image
                icon_path = self.assets_path / 'images' / 'items' / image_filename
                if icon_path.exists():
                    try:
                        ico = pygame.image.load(str(icon_path)).convert_alpha()
                        ico = pygame.transform.smoothscale(ico, (ico_rect.w, ico_rect.h))
                        self.screen.blit(ico, ico_rect)
                    except Exception:
                        # If loading fails, draw placeholder
                        pygame.draw.rect(self.screen, (100, 100, 140), ico_rect, border_radius=4)
                else:
                    # Image file doesn't exist, draw placeholder
                    pygame.draw.rect(self.screen, (100, 100, 140), ico_rect, border_radius=4)
            else:
                # No image specified, draw placeholder
                pygame.draw.rect(self.screen, (100, 100, 140), ico_rect, border_radius=4)
            
            # Count badge
            badge_rect = pygame.Rect(cx + cell_w - 24, cy + 6, 18, 14)
            pygame.draw.rect(self.screen, (10, 10, 10), badge_rect, border_radius=3)
            self._blit_text_outlined(self.screen, self.small_font, str(cnt), badge_rect.center, fg=(255,255,255), outline=(0,0,0), outline_width=1, center=True)
            
            # Item name at bottom of cell, scaled to fit (use rarity color)
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
                
                # Draw name at bottom of cell with rarity color
                name_y = cy + cell_h - 18
                rarity = item_def.get('rarity', 'common') if item_def else 'common'
                name_color = self.get_rarity_color(rarity)
                outline_color = (255, 255, 255) if rarity == 'ancient' else (0, 0, 0)
                outline_width = 2 if rarity == 'ancient' else 1
                self._blit_text_outlined(self.screen, self.small_font, name_text, (cx + 4, name_y), fg=name_color, outline=outline_color, outline_width=outline_width)
            
            # Register for clicks
            self.inventory_cells.append({'rect': rect, 'item_id': iid, 'count': cnt, 'def': item_def})
        
        # Selected item details
        if self.inventory_selected:
            if self.inventory_selected not in [iid for iid, _ in items]:
                self.inventory_selected = None

        if self.inventory_selected:
            sel = None
            for c in self.inventory_cells:
                if c['item_id'] == self.inventory_selected:
                    sel = c
                    break
            
            if sel:
                detail_y = start_y + 3 * (cell_h + pad) + 20
                detail_rect = pygame.Rect(modal_x + 30, detail_y, modal_w - 60, 120)
                pygame.draw.rect(self.screen, (40, 40, 60), detail_rect, border_radius=6)
                
                # Item name with rarity color at top of details panel
                item_name = sel['def'].get('name', sel['item_id']) if sel.get('def') else sel['item_id']
                rarity = sel['def'].get('rarity', 'common') if sel.get('def') else 'common'
                name_color = self.get_rarity_color(rarity)
                outline_color = (255, 255, 255) if rarity == 'ancient' else (0, 0, 0)
                outline_width = 2 if rarity == 'ancient' else 1
                self._blit_text_outlined(self.screen, self.small_font, item_name[:35], (detail_rect.x + 10, detail_rect.y + 5), fg=name_color, outline=outline_color, outline_width=outline_width)
                
                # Description
                desc = sel['def'].get('description', 'No description') if sel.get('def') else 'No description'
                self._blit_text_outlined(self.screen, pygame.font.Font(None, 22), desc[:80], (detail_rect.x + 10, detail_rect.y + 28), fg=(180,180,180), outline=(0,0,0), outline_width=1)
                
                # Stats display
                if sel.get('def'):
                    stats_y = detail_rect.y + 50
                    stats = []
                    item_def = sel['def']
                    if item_def.get('attack'): stats.append(f"+{item_def['attack']} Attack")
                    if item_def.get('defense'): stats.append(f"+{item_def['defense']} Defense")
                    if item_def.get('max_hp'): stats.append(f"+{item_def['max_hp']} Max HP")
                    if item_def.get('penetration'): stats.append(f"+{item_def['penetration']:.0f} Penetration")
                    if item_def.get('magic_power'): stats.append(f"+{item_def['magic_power']} Magic Power")
                    if item_def.get('magic_penetration'): stats.append(f"+{item_def['magic_penetration']:.0f} Magic Pen")
                    if item_def.get('max_mana'): stats.append(f"+{item_def['max_mana']} Max Mana")
                    if item_def.get('mana_regen'): stats.append(f"+{item_def['mana_regen']} Mana Regen")
                    
                    for i, stat in enumerate(stats[:4]):  # Show up to 4 stats
                        col = i % 2
                        row = i // 2
                        stat_x = detail_rect.x + 10 + col * 200
                        stat_y = stats_y + row * 20
                        self._blit_text_outlined(self.screen, self.small_font, stat, (stat_x, stat_y), fg=(150,220,150), outline=(0,0,0), outline_width=1)
                
                # Action buttons
                btn_y = detail_rect.y + 85
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
                    # Multiple use buttons for consumables
                    current_qty = sel.get('count', 1)
                    btn_width = 50
                    btn_spacing = 5
                    start_x = detail_rect.x + detail_rect.w - (btn_width * 5 + btn_spacing * 4)
                    
                    use_amounts = [1, 5, 10, 100, current_qty]  # Last one is "All"
                    use_labels = ['x1', 'x5', 'x10', 'x100', 'All']
                    
                    for i, (amount, label) in enumerate(zip(use_amounts, use_labels)):
                        if amount > current_qty and label != 'All':
                            continue  # Skip if not enough items
                        
                        actual_amount = min(amount, current_qty) if label != 'All' else current_qty
                        btn_x = start_x + i * (btn_width + btn_spacing)
                        use_rect = pygame.Rect(btn_x, btn_y, btn_width, 30)
                        
                        # Color gradient based on amount
                        if label == 'All':
                            color = (220, 100, 100)
                        else:
                            intensity = min(255, 140 + i * 20)
                            color = (intensity, 120, 60)
                        
                        pygame.draw.rect(self.screen, color, use_rect, border_radius=6)
                        use_text = self.small_font.render(label, True, (0, 0, 0))
                        self.screen.blit(use_text, use_text.get_rect(center=use_rect.center))
                        
                        def make_use(iid=sel['item_id'], qty=actual_amount):
                            def act():
                                # Use multiple items
                                effect_mgr = getattr(battle, 'effect_manager', None) if battle else None
                                old_hp = getattr(player, 'hp', 0)
                                used_count = 0
                                for _ in range(qty):
                                    if player.use_item(iid, effect_mgr):
                                        used_count += 1
                                    else:
                                        break
                                
                                new_hp = getattr(player, 'hp', 0)
                                heal_amount = new_hp - old_hp
                                if battle and heal_amount > 0:
                                    try:
                                        battle.damage_events.append({
                                            'target': 'player',
                                            'amount': int(heal_amount),
                                            'time': time.time(),
                                            'is_heal': True,
                                        })
                                    except Exception:
                                        pass
                                
                                if battle and hasattr(battle, 'add_log') and used_count > 0:
                                    battle.add_log(f"Used {sel['def'].get('name', iid)} x{used_count}", 'info')
                                
                                if getattr(battle, 'turn', None) == 'player':
                                    battle.turn = 'enemy'
                                    battle.last_action_time = time.time()
                                    battle.action_delay = 1.2
                                    battle.enemy_turn_processed = False
                                self.inventory_selected = None
                            return act
                        self.character_sheet_buttons.append({'rect': use_rect, 'action': make_use()})
                elif sel.get('def') and sel['def'].get('type') == 'container':
                    # Container - add multiple Open buttons
                    current_qty = sel.get('count', 1)
                    btn_width = 50
                    btn_spacing = 5
                    start_x = detail_rect.x + detail_rect.w - (btn_width * 5 + btn_spacing * 4)
                    
                    open_amounts = [1, 5, 10, 100, current_qty]  # Last one is "All"
                    open_labels = ['x1', 'x5', 'x10', 'x100', 'All']
                    
                    for i, (amount, label) in enumerate(zip(open_amounts, open_labels)):
                        if amount > current_qty and label != 'All':
                            continue  # Skip if not enough items
                        
                        actual_amount = min(amount, current_qty) if label != 'All' else current_qty
                        btn_x = start_x + i * (btn_width + btn_spacing)
                        open_rect = pygame.Rect(btn_x, btn_y, btn_width, 30)
                        
                        # Color gradient based on amount
                        if label == 'All':
                            color = (220, 160, 60)
                        else:
                            intensity = min(255, 160 + i * 15)
                            color = (intensity, 140 + i * 10, 60)
                        
                        pygame.draw.rect(self.screen, color, open_rect, border_radius=6)
                        open_text = self.small_font.render(label, True, (0, 0, 0))
                        self.screen.blit(open_text, open_text.get_rect(center=open_rect.center))
                        
                        def make_open(iid=sel['item_id'], idef=sel.get('def'), qty=actual_amount):
                            def act():
                                # Open multiple containers
                                all_granted = []
                                for _ in range(qty):
                                    if player.has_item(iid):
                                        granted = player.open_container(idef)
                                        player.remove_item(iid, 1)
                                        all_granted.extend(granted)
                                    else:
                                        break
                                
                                # Add combat log messages if battle exists
                                if battle and hasattr(battle, 'add_log') and all_granted:
                                    # Aggregate results
                                    skill_upgrades = {}
                                    item_counts = {}
                                    for grant_type, grant_id, qty_or_level in all_granted:
                                        if grant_type == 'skill':
                                            if grant_id not in skill_upgrades:
                                                skill_upgrades[grant_id] = []
                                            skill_upgrades[grant_id].append(qty_or_level)
                                        elif grant_type == 'item':
                                            item_counts[grant_id] = item_counts.get(grant_id, 0) + qty_or_level
                                    
                                    for skill_id, levels in skill_upgrades.items():
                                        battle.add_log(f"Skill: {skill_id} (x{len(levels)} upgrades)!", 'buff')
                                    for item_id, total_qty in item_counts.items():
                                        battle.add_log(f"Received: {item_id} x{total_qty}!", 'info')
                                
                                self.inventory_selected = None
                            return act
                        self.character_sheet_buttons.append({'rect': open_rect, 'action': make_open()})
    
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
            (f"  Game Seed: {getattr(player, 'game_seed', 'N/A')}", (180, 180, 255)),
            ("", None),
            ("Combat Stats", None),
            (f"  HP: {player.hp} / {player.max_hp}", (100, 255, 100)),
            (f"  Attack: {player.atk}", (255, 150, 100)),
            (f"  Defense: {player.defense} ({def_pct:.1f}% reduction)", (150, 200, 255)),
            (f"  Penetration: {getattr(player, 'penetration', 0):.1f} ({pen_pct:.1f}%)", (255, 180, 255)),
            ("", None),
            ("Magic Stats", None),
            (f"  Mana: {getattr(player, 'current_mana', 0)} / {getattr(player, 'max_mana', 0)}", (100, 200, 255)),
            (f"  Mana Regen: {getattr(player, 'mana_regen', 0)}/turn", (150, 220, 255)),
            (f"  Magic Power: {getattr(player, 'magic_power', 0)}", (200, 150, 255)),
            (f"  Magic Penetration: {getattr(player, 'magic_penetration', 0)}", (220, 170, 255)),
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
    
    def _draw_skills_ui(self, player, battle):
        """Draw Skills UI modal with unlocked skills, lock status, and equip options with scrolling"""
        modal_w, modal_h = 700, 520
        modal_x = (self.screen.get_width() - modal_w) // 2
        # Position higher to avoid overlap with bottom buttons
        modal_y = max(20, (self.screen.get_height() - modal_h) // 2 - 30)
        
        # Reset buttons list
        self.skills_ui_buttons = []
        
        # Modal background
        modal_surf = pygame.Surface((modal_w, modal_h))
        modal_surf.fill((30, 30, 40))
        self.screen.blit(modal_surf, (modal_x, modal_y))
        
        # Title bar
        title_bar = pygame.Rect(modal_x, modal_y, modal_w, 45)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bar)
        self._blit_text_outlined(self.screen, self.title_font, "Skills", (modal_x + 20, modal_y + 12), fg=(255,255,255), outline=(0,0,0), outline_width=2)
        
        # Close button
        close_rect = pygame.Rect(modal_x + modal_w - 90, modal_y + 10, 80, 30)
        pygame.draw.rect(self.screen, (180, 80, 80), close_rect, border_radius=6)
        ct = self.small_font.render('Close', True, (0, 0, 0))
        self.screen.blit(ct, ct.get_rect(center=close_rect.center))
        self.skills_ui_buttons.append({'rect': close_rect, 'action': lambda: setattr(self, 'skills_ui_open', False)})
        
        # Get all skills and player's unlocked skills
        all_skills = battle.skill_manager.skills if hasattr(battle, 'skill_manager') else {}
        unlocked_skills = getattr(player, 'skills', [])
        equipped_skills = getattr(player, 'equipped_skills', [])[:5]  # Max 5 equipped
        
        # Split into unlocked and locked
        unlocked_list = [(sid, all_skills[sid]) for sid in unlocked_skills if sid in all_skills]
        # Filter locked skills: only show if unlock requirement is level-based (class level)
        locked_list = []
        for sid, skill in all_skills.items():
            if sid not in unlocked_skills:
                # Only show locked skill if it has a level requirement
                requirements = skill.get('unlock_requirements', {})
                if 'level' in requirements:
                    locked_list.append((sid, skill))
        
        # Content area with scrolling
        content_y = modal_y + 50
        content_h = modal_h - 60
        
        # Create scrollable surface
        skill_w = 200
        skill_h = 80
        cols = 3
        
        # Calculate total height needed
        unlocked_rows = (len(unlocked_list) + cols - 1) // cols
        locked_rows = (len(locked_list) + cols - 1) // cols
        total_content_height = 40 + unlocked_rows * (skill_h + 10) + 60 + locked_rows * (skill_h + 10)
        
        # Max scroll
        max_scroll = max(0, total_content_height - content_h)
        self.skills_scroll = max(0, min(self.skills_scroll, max_scroll))
        
        # Scroll buttons
        if max_scroll > 0:
            # Up button
            up_rect = pygame.Rect(modal_x + modal_w - 40, modal_y + 50, 30, 30)
            pygame.draw.rect(self.screen, (100, 100, 120), up_rect, border_radius=4)
            up_text = self.small_font.render('▲', True, (255, 255, 255))
            self.screen.blit(up_text, up_text.get_rect(center=up_rect.center))
            self.skills_ui_buttons.append({'rect': up_rect, 'action': lambda: setattr(self, 'skills_scroll', max(0, self.skills_scroll - 50))})
            
            # Down button
            down_rect = pygame.Rect(modal_x + modal_w - 40, modal_y + modal_h - 40, 30, 30)
            pygame.draw.rect(self.screen, (100, 100, 120), down_rect, border_radius=4)
            down_text = self.small_font.render('▼', True, (255, 255, 255))
            self.screen.blit(down_text, down_text.get_rect(center=down_rect.center))
            self.skills_ui_buttons.append({'rect': down_rect, 'action': lambda: setattr(self, 'skills_scroll', min(max_scroll, self.skills_scroll + 50))})
        
        # Create clipping rect for scrollable content
        clip_rect = pygame.Rect(modal_x, content_y, modal_w - 50, content_h)
        self.screen.set_clip(clip_rect)
        
        # Draw unlocked skills section
        section_y = content_y + 10 - self.skills_scroll
        self._blit_text_outlined(self.screen, self.small_font, f"Unlocked Skills ({len(unlocked_list)})", (modal_x + 20, section_y), fg=(100, 255, 100), outline=(0,0,0), outline_width=2)
        
        grid_y = section_y + 30
        grid_x = modal_x + 20
        
        for idx, (skill_id, skill) in enumerate(unlocked_list):
            col = idx % cols
            row = idx // cols
            sx = grid_x + col * (skill_w + 10)
            sy = grid_y + row * (skill_h + 10)
            
            # Skip if outside visible area
            if sy + skill_h < content_y or sy > content_y + content_h:
                continue
            
            # Skill box
            is_equipped = skill_id in equipped_skills
            box_color = (80, 120, 80) if is_equipped else (60, 60, 90)
            skill_rect = pygame.Rect(sx, sy, skill_w, skill_h)
            pygame.draw.rect(self.screen, box_color, skill_rect, border_radius=6)
            
            # Get skill level
            skill_level = getattr(player, 'skill_levels', {}).get(skill_id, 1)
            
            # Skill name with level
            skill_name = skill.get('name', skill_id)[:18]
            if skill_level > 1:
                skill_name_text = f"{skill_name} Lv{skill_level}"
                name_color = (255, 255, 100)  # Yellow for leveled skills
            else:
                skill_name_text = skill_name
                name_color = (255, 255, 255)
            self._blit_text_outlined(self.screen, self.small_font, skill_name_text, (sx + 5, sy + 5), fg=name_color, outline=(0,0,0), outline_width=1)
            
            # Mana cost (scaled by level)
            base_mana_cost = skill.get('mana_cost', 0)
            actual_mana_cost = int(base_mana_cost * (1 + (skill_level - 1) * 0.2))
            if skill_level > 1:
                mana_text = f"Mana: {actual_mana_cost} ({base_mana_cost}+{skill_level-1})"
            else:
                mana_text = f"Mana: {actual_mana_cost}"
            self._blit_text_outlined(self.screen, self.small_font, mana_text, (sx + 5, sy + 25), fg=(100, 150, 255), outline=(0,0,0), outline_width=1)
            
            # Type and element
            skill_type = skill.get('type', '?')
            element = skill.get('element', 'neutral')
            info_text = f"{skill_type.capitalize()} / {element.capitalize()}"
            self._blit_text_outlined(self.screen, self.small_font, info_text[:25], (sx + 5, sy + 42), fg=(200, 200, 200), outline=(0,0,0), outline_width=1)
            
            # Equip/Unequip button
            if is_equipped:
                btn_rect = pygame.Rect(sx + skill_w - 75, sy + skill_h - 28, 70, 24)
                pygame.draw.rect(self.screen, (180, 80, 80), btn_rect, border_radius=4)
                btn_text = self.small_font.render('Unequip', True, (0, 0, 0))
                self.screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))
                self.skills_ui_buttons.append({'rect': btn_rect, 'action': lambda sid=skill_id: self._unequip_skill(player, sid)})
            else:
                if len(equipped_skills) < 5:
                    btn_rect = pygame.Rect(sx + skill_w - 75, sy + skill_h - 28, 70, 24)
                    pygame.draw.rect(self.screen, (80, 180, 80), btn_rect, border_radius=4)
                    btn_text = self.small_font.render('Equip', True, (0, 0, 0))
                    self.screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))
                    self.skills_ui_buttons.append({'rect': btn_rect, 'action': lambda sid=skill_id: self._equip_skill(player, sid)})
        
        # Draw locked skills section
        locked_section_y = grid_y + unlocked_rows * (skill_h + 10) + 20
        self._blit_text_outlined(self.screen, self.small_font, f"Locked Skills ({len(locked_list)})", (modal_x + 20, locked_section_y), fg=(255, 100, 100), outline=(0,0,0), outline_width=2)
        
        locked_grid_y = locked_section_y + 30
        for idx, (skill_id, skill) in enumerate(locked_list):
            col = idx % cols
            row = idx // cols
            sx = grid_x + col * (skill_w + 10)
            sy = locked_grid_y + row * (skill_h + 10)
            
            # Skip if outside visible area
            if sy + skill_h < content_y or sy > content_y + content_h:
                continue
            
            # Locked skill box (dimmed)
            skill_rect = pygame.Rect(sx, sy, skill_w, skill_h)
            pygame.draw.rect(self.screen, (40, 40, 50), skill_rect, border_radius=6)
            
            # Skill name (grayed out)
            skill_name = skill.get('name', skill_id)[:20]
            self._blit_text_outlined(self.screen, self.small_font, skill_name, (sx + 5, sy + 5), fg=(120, 120, 120), outline=(0,0,0), outline_width=1)
            
            # Lock icon
            lock_text = "🔒 LOCKED"
            self._blit_text_outlined(self.screen, self.small_font, lock_text, (sx + 5, sy + 25), fg=(180, 80, 80), outline=(0,0,0), outline_width=1)
            
            # Unlock requirements (if defined)
            requirements = skill.get('unlock_requirements', {})
            if requirements:
                req_level = requirements.get('level')
                req_item = requirements.get('item_equipped')
                if req_level:
                    req_text = f"Req: Lvl {req_level}"
                    self._blit_text_outlined(self.screen, self.small_font, req_text, (sx + 5, sy + 45), fg=(180, 180, 100), outline=(0,0,0), outline_width=1)
                elif req_item:
                    req_text = f"Req: {req_item[:15]}"
                    self._blit_text_outlined(self.screen, self.small_font, req_text, (sx + 5, sy + 45), fg=(180, 180, 100), outline=(0,0,0), outline_width=1)
        
        # Reset clip
        self.screen.set_clip(None)
    
    def _equip_skill(self, player, skill_id):
        """Equip a skill to active skill bar"""
        if not hasattr(player, 'equipped_skills'):
            player.equipped_skills = []
        if len(player.equipped_skills) < 5 and skill_id not in player.equipped_skills:
            player.equipped_skills.append(skill_id)
    
    def _unequip_skill(self, player, skill_id):
        """Unequip a skill from active skill bar"""
        if hasattr(player, 'equipped_skills') and skill_id in player.equipped_skills:
            player.equipped_skills.remove(skill_id)
    
    def _use_skill_slot(self, slot_index):
        """Use skill in the given slot (0-4)"""
        if not hasattr(self, 'battle') or self.battle is None:
            return
        player = self.battle.player
        if not hasattr(player, 'equipped_skills'):
            return
        if slot_index >= len(player.equipped_skills):
            return
        skill_id = player.equipped_skills[slot_index]
        if hasattr(self.battle, 'player_use_skill'):
            self.battle.player_use_skill(skill_id)
    
    def _draw_crafting_ui(self, player, battle):
        """Draw Crafting UI modal with recipes and crafting functionality"""
        modal_w, modal_h = 900, 600
        modal_x = (self.screen.get_width() - modal_w) // 2
        modal_y = (self.screen.get_height() - modal_h) // 2
        
        # Reset buttons list
        self.crafting_ui_buttons = []
        
        # Modal background
        modal_surf = pygame.Surface((modal_w, modal_h))
        modal_surf.fill((30, 30, 40))
        self.screen.blit(modal_surf, (modal_x, modal_y))
        
        # Title bar
        title_bar = pygame.Rect(modal_x, modal_y, modal_w, 45)
        pygame.draw.rect(self.screen, (40, 40, 60), title_bar)
        self._blit_text_outlined(self.screen, self.title_font, "Crafting", (modal_x + 20, modal_y + 12), fg=(255,255,255), outline=(0,0,0), outline_width=2)
        
        # Close button
        close_rect = pygame.Rect(modal_x + modal_w - 90, modal_y + 10, 80, 30)
        pygame.draw.rect(self.screen, (180, 80, 80), close_rect, border_radius=6)
        ct = self.small_font.render('Close', True, (0, 0, 0))
        self.screen.blit(ct, ct.get_rect(center=close_rect.center))
        self.crafting_ui_buttons.append({'rect': close_rect, 'action': lambda: setattr(self, 'crafting_ui_open', False)})
        
        # Get crafting system from battle
        crafting_system = getattr(battle, 'crafting_system', None) if battle else None
        if not crafting_system:
            # No crafting system available
            error_text = "Crafting system not available"
            self._blit_text_outlined(self.screen, self.title_font, error_text, (modal_x + modal_w // 2, modal_y + modal_h // 2), fg=(255,100,100), outline=(0,0,0), outline_width=2, center=True)
            return
        
        recipes = crafting_system.get_all_recipes()
        if not recipes:
            # No recipes available
            error_text = "No recipes available"
            self._blit_text_outlined(self.screen, self.title_font, error_text, (modal_x + modal_w // 2, modal_y + modal_h // 2), fg=(255,100,100), outline=(0,0,0), outline_width=2, center=True)
            return
        
        # Get player's inventory
        player_inventory = getattr(player, 'inventory', {})
        player_level = getattr(player, 'level', 1)
        
        # Initialize crafting page if not exists
        if not hasattr(self, 'crafting_page'):
            self.crafting_page = 0
        
        # Pagination settings
        recipes_per_page = 6
        total_pages = (len(recipes) + recipes_per_page - 1) // recipes_per_page
        self.crafting_page = max(0, min(self.crafting_page, total_pages - 1))
        
        # Get current page recipes
        start_idx = self.crafting_page * recipes_per_page
        end_idx = min(start_idx + recipes_per_page, len(recipes))
        page_recipes = recipes[start_idx:end_idx]
        
        # Left panel - Recipe list
        list_x = modal_x + 20
        list_y = modal_y + 60
        list_w = 350
        list_h = modal_h - 120  # Leave space for pagination buttons
        
        # Draw recipe list background
        pygame.draw.rect(self.screen, (40, 40, 55), (list_x, list_y, list_w, list_h), border_radius=8)
        
        # Recipe list title
        self._blit_text_outlined(self.screen, self.small_font, "Recipes", (list_x + 10, list_y + 5), fg=(255, 220, 100), outline=(0,0,0), outline_width=2)
        
        # Draw recipe entries
        entry_y = list_y + 35
        entry_h = 70
        entry_pad = 5
        
        for recipe in page_recipes:
            recipe_id = recipe.get('id')
            recipe_name = recipe.get('name', recipe_id)
            category = recipe.get('category', 'misc')
            
            # Check if can craft
            can_craft, reason = crafting_system.can_craft(recipe_id, player_inventory, player_level)
            
            # Recipe entry box
            is_selected = (self.crafting_selected_recipe == recipe_id)
            if is_selected:
                box_color = (80, 120, 160)
            elif can_craft:
                box_color = (60, 100, 60)
            else:
                box_color = (60, 60, 80)
            
            entry_rect = pygame.Rect(list_x + 10, entry_y, list_w - 20, entry_h)
            pygame.draw.rect(self.screen, box_color, entry_rect, border_radius=6)
            
            if is_selected:
                pygame.draw.rect(self.screen, (150, 180, 220), entry_rect, 3, border_radius=6)
            
            # Recipe name
            self._blit_text_outlined(self.screen, self.small_font, recipe_name[:30], (entry_rect.x + 8, entry_rect.y + 8), fg=(255, 255, 255), outline=(0,0,0), outline_width=1)
            
            # Category badge
            cat_color_map = {
                'weapon': (255, 150, 100),
                'armor': (150, 200, 255),
                'consumable': (100, 255, 150),
                'offhand': (200, 150, 255),
                'material': (200, 200, 100),
                'misc': (180, 180, 180)
            }
            cat_color = cat_color_map.get(category, (180, 180, 180))
            cat_text = category.upper()
            self._blit_text_outlined(self.screen, self.small_font, cat_text, (entry_rect.x + 8, entry_rect.y + 28), fg=cat_color, outline=(0,0,0), outline_width=1)
            
            # Craftable status
            status_text = "✓ Can Craft" if can_craft else f"✗ {reason}"
            status_color = (100, 255, 100) if can_craft else (255, 100, 100)
            self._blit_text_outlined(self.screen, self.small_font, status_text[:25], (entry_rect.x + 8, entry_rect.y + 48), fg=status_color, outline=(0,0,0), outline_width=1)
            
            # Click to select
            self.crafting_ui_buttons.append({'rect': entry_rect, 'action': lambda rid=recipe_id: setattr(self, 'crafting_selected_recipe', rid)})
            
            entry_y += entry_h + entry_pad
        
        # Pagination buttons
        if total_pages > 1:
            btn_y = modal_y + modal_h - 50
            prev_btn = pygame.Rect(list_x + 10, btn_y, 100, 35)
            next_btn = pygame.Rect(list_x + list_w - 110, btn_y, 100, 35)
            
            # Previous button
            prev_enabled = self.crafting_page > 0
            prev_color = (80, 120, 200) if prev_enabled else (60, 60, 80)
            pygame.draw.rect(self.screen, prev_color, prev_btn, border_radius=6)
            prev_text = self.small_font.render("< Prev", True, (255, 255, 255) if prev_enabled else (120, 120, 120))
            self.screen.blit(prev_text, prev_text.get_rect(center=prev_btn.center))
            if prev_enabled:
                self.crafting_ui_buttons.append({'rect': prev_btn, 'action': lambda: setattr(self, 'crafting_page', max(0, self.crafting_page - 1))})
            
            # Next button
            next_enabled = self.crafting_page < total_pages - 1
            next_color = (80, 120, 200) if next_enabled else (60, 60, 80)
            pygame.draw.rect(self.screen, next_color, next_btn, border_radius=6)
            next_text = self.small_font.render("Next >", True, (255, 255, 255) if next_enabled else (120, 120, 120))
            self.screen.blit(next_text, next_text.get_rect(center=next_btn.center))
            if next_enabled:
                self.crafting_ui_buttons.append({'rect': next_btn, 'action': lambda: setattr(self, 'crafting_page', min(total_pages - 1, self.crafting_page + 1))})
            
            # Page indicator
            page_text = self.small_font.render(f"Page {self.crafting_page + 1}/{total_pages}", True, (200, 200, 220))
            self.screen.blit(page_text, page_text.get_rect(center=(list_x + list_w // 2, btn_y + 17)))
        
        # Right panel - Recipe details and crafting
        if self.crafting_selected_recipe:
            selected_recipe = crafting_system.get_recipe_by_id(self.crafting_selected_recipe)
            if selected_recipe:
                detail_x = list_x + list_w + 20
                detail_y = modal_y + 60
                detail_w = modal_w - (detail_x - modal_x) - 20
                detail_h = modal_h - 80
                
                # Draw detail background
                pygame.draw.rect(self.screen, (40, 40, 55), (detail_x, detail_y, detail_w, detail_h), border_radius=8)
                
                # Recipe name
                dy = detail_y + 15
                recipe_name = selected_recipe.get('name', 'Unknown')
                self._blit_text_outlined(self.screen, self.title_font, recipe_name[:25], (detail_x + 15, dy), fg=(255, 255, 100), outline=(0,0,0), outline_width=2)
                dy += 40
                
                # Description
                desc = selected_recipe.get('description', 'No description')
                self._blit_text_outlined(self.screen, self.small_font, desc[:50], (detail_x + 15, dy), fg=(200, 200, 200), outline=(0,0,0), outline_width=1)
                dy += 30
                
                # Divider line
                pygame.draw.line(self.screen, (100, 100, 120), (detail_x + 15, dy), (detail_x + detail_w - 15, dy), 2)
                dy += 20
                
                # Ingredients section
                self._blit_text_outlined(self.screen, self.small_font, "Required Ingredients:", (detail_x + 15, dy), fg=(150, 200, 255), outline=(0,0,0), outline_width=2)
                dy += 30
                
                ingredients = selected_recipe.get('ingredients', [])
                for ingredient in ingredients:
                    item_id = ingredient.get('item_id')
                    required_qty = ingredient.get('quantity', 1)
                    current_qty = player_inventory.get(item_id, 0)
                    
                    # Get item name
                    item_def = self.shop_loader.find_item(item_id) if self.shop_loader else None
                    item_name = item_def.get('name') if item_def else item_id
                    
                    # Ingredient text
                    has_enough = current_qty >= required_qty
                    ing_text = f"  • {item_name}: {current_qty}/{required_qty}"
                    ing_color = (100, 255, 100) if has_enough else (255, 100, 100)
                    self._blit_text_outlined(self.screen, self.small_font, ing_text[:40], (detail_x + 15, dy), fg=ing_color, outline=(0,0,0), outline_width=1)
                    dy += 25
                
                dy += 20
                
                # Result section
                self._blit_text_outlined(self.screen, self.small_font, "Result:", (detail_x + 15, dy), fg=(150, 255, 200), outline=(0,0,0), outline_width=2)
                dy += 30
                
                result_item_id = selected_recipe.get('result_item_id')
                result_qty = selected_recipe.get('result_quantity', 1)
                
                # Get result item name
                result_def = self.shop_loader.find_item(result_item_id) if self.shop_loader else None
                result_name = result_def.get('name') if result_def else result_item_id
                
                result_text = f"  {result_name} x{result_qty}"
                self._blit_text_outlined(self.screen, self.small_font, result_text[:40], (detail_x + 15, dy), fg=(255, 255, 150), outline=(0,0,0), outline_width=1)
                dy += 40
                
                # Level requirement
                required_level = selected_recipe.get('required_level', 1)
                if required_level > 1:
                    level_text = f"Required Level: {required_level}"
                    level_color = (100, 255, 100) if player_level >= required_level else (255, 100, 100)
                    self._blit_text_outlined(self.screen, self.small_font, level_text, (detail_x + 15, dy), fg=level_color, outline=(0,0,0), outline_width=1)
                    dy += 30
                
                # Craft button
                can_craft, reason = crafting_system.can_craft(self.crafting_selected_recipe, player_inventory, player_level)
                
                craft_btn_w = 200
                craft_btn_h = 50
                craft_btn_x = detail_x + (detail_w - craft_btn_w) // 2
                craft_btn_y = detail_y + detail_h - craft_btn_h - 20
                
                craft_rect = pygame.Rect(craft_btn_x, craft_btn_y, craft_btn_w, craft_btn_h)
                
                if can_craft:
                    pygame.draw.rect(self.screen, (80, 180, 80), craft_rect, border_radius=8)
                    craft_text = "CRAFT"
                    text_color = (0, 0, 0)
                    
                    def craft_action():
                        success, msg, result_item, result_count = crafting_system.craft_item(
                            self.crafting_selected_recipe,
                            player_inventory,
                            player_level
                        )
                        if success and battle:
                            battle.add_log(msg, 'buff')
                        elif not success and battle:
                            battle.add_log(msg, 'info')
                    
                    self.crafting_ui_buttons.append({'rect': craft_rect, 'action': craft_action})
                else:
                    pygame.draw.rect(self.screen, (80, 80, 80), craft_rect, border_radius=8)
                    craft_text = "CANNOT CRAFT"
                    text_color = (150, 150, 150)
                
                self._blit_text_outlined(self.screen, self.title_font, craft_text, craft_rect.center, fg=text_color, outline=(0,0,0) if can_craft else (50,50,50), outline_width=2, center=True)
                
                # Show reason if can't craft
                if not can_craft:
                    reason_y = craft_btn_y - 25
                    self._blit_text_outlined(self.screen, self.small_font, reason, (detail_x + detail_w // 2, reason_y), fg=(255, 150, 100), outline=(0,0,0), outline_width=1, center=True)
    
    def _draw_combat_log(self, battle):
        """Draw draggable combat log window"""
        if not getattr(self, 'combat_log_open', False):
            return
        
        if battle is None or not hasattr(battle, 'combat_log'):
            return
        
        # Window dimensions
        log_w, log_h = 300, 400
        
        # Use stored position or default to right side
        if self.combat_log_pos is None:
            log_x = self.screen.get_width() - log_w - 20
            log_y = 80
            self.combat_log_pos = (log_x, log_y)
        else:
            log_x, log_y = self.combat_log_pos
        
        # Background
        bg_rect = pygame.Rect(log_x, log_y, log_w, log_h)
        pygame.draw.rect(self.screen, (30, 30, 40, 240), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), bg_rect, 2, border_radius=10)
        
        # Title bar (draggable)
        title_bar = pygame.Rect(log_x, log_y, log_w, 30)
        pygame.draw.rect(self.screen, (50, 50, 70), title_bar, border_radius=10)
        title_text = self.small_font.render("Combat Log", True, (255, 255, 255))
        self.screen.blit(title_text, (log_x + 10, log_y + 5))
        self.combat_log_title_bar = title_bar
        
        # Get recent log entries (last 20)
        log_entries = battle.combat_log[-20:]
        
        # Draw log entries from bottom to top (newest at bottom)
        entry_y = log_y + log_h - 35
        line_height = 18
        
        for entry in reversed(log_entries):
            if entry_y <= log_y + 35:
                break  # Reached top of visible area
            
            msg = entry.get('message', '')
            category = entry.get('category', 'info')
            
            # Color based on category
            color_map = {
                'damage': (255, 100, 100),
                'heal': (100, 255, 100),
                'buff': (100, 200, 255),
                'debuff': (255, 150, 100),
                'info': (200, 200, 200),
                'skill': (200, 150, 255),
            }
            color = color_map.get(category, (200, 200, 200))
            
            # Render message (truncate if too long)
            if len(msg) > 35:
                msg = msg[:32] + "..."
            
            msg_surf = self.small_font.render(msg, True, color)
            self.screen.blit(msg_surf, (log_x + 10, entry_y))
            entry_y -= line_height