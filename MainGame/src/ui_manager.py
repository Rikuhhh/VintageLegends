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
        # inventory modal
        self.inventory_open = False
        self.inventory_buttons = []
        self.inventory_cells = []
        self.inventory_selected = None

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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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

            # inventory modal buttons
            # inventory cell clicks & action buttons
            for btn in getattr(self, 'inventory_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return
            for cell in getattr(self, 'inventory_cells', []):
                if cell['rect'].collidepoint(event.pos):
                    # select this item
                    self.inventory_selected = cell['item_id']
                    return

            # inventory open/close button on main panel
            if getattr(self, 'inventory_open_rect', None) and self.inventory_open_rect.collidepoint(event.pos):
                self.inventory_open = not self.inventory_open
                return

    def update(self, player, battle):
        # Méthode disponible si on veut animer ou mettre à jour des composants UI
        return

    def draw(self, player=None, battle=None):
        # Draw a background panel for UI (image if available, otherwise a semi-transparent rect)
        screen_w, screen_h = self.screen.get_size()
        panel_w = 360
        panel_h = 260
        panel_x = 10
        panel_y = 10
        if self.panel_image:
            # scale to fit panel area if needed
            img = pygame.transform.smoothscale(self.panel_image, (panel_w, panel_h))
            self.screen.blit(img, (panel_x, panel_y))
        else:
            s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            s.fill((20, 20, 30, 200))  # semi-transparent dark panel
            # rounded rect isn't in older pygame, draw basic rect for compatibility
            self.screen.blit(s, (panel_x, panel_y))

        # Dessine les boutons
        for btn in self.buttons:
            pygame.draw.rect(self.screen, (100, 100, 250), btn["rect"], border_radius=8)
            text = self.title_font.render(btn["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)

        # Affichage des infos joueur / ennemi
        x = panel_x + 12
        y = panel_y + 12
        line_h = 30

        if player is not None:
            hp_text = self.small_font.render(f"Player HP: {player.hp}/{player.max_hp}", True, (255, 255, 255))
            self.screen.blit(hp_text, (x, y))
            y += line_h

        if battle is not None and getattr(battle, "enemy", None):
            enemy = battle.enemy
            name_text = self.small_font.render(f"Enemy: {getattr(enemy, 'name', 'Unknown')}", True, (255, 200, 200))
            self.screen.blit(name_text, (x, y))
            y += line_h

            hp_text = self.small_font.render(f"Enemy HP: {enemy.hp}/{enemy.max_hp}", True, (255, 150, 150))
            self.screen.blit(hp_text, (x, y))
            y += line_h

            # Barre de vie
            bar_x, bar_y = x, y
            bar_width, bar_height = 200, 20
            hp_ratio = (enemy.hp / enemy.max_hp) if getattr(enemy, "max_hp", 1) > 0 else 0
            pygame.draw.rect(self.screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
            hp_bar_label = self.small_font.render(f"{enemy.hp}/{enemy.max_hp}", True, (255, 255, 255))
            self.screen.blit(hp_bar_label, (bar_x + bar_width + 10, bar_y))
            y += bar_height + 10

        # Stats joueur (gold, level)
        if player is not None:
            gold = getattr(player, "gold", 0)
            gold_text = self.small_font.render(f"Gold: {gold}", True, (255, 215, 0))
            self.screen.blit(gold_text, (x, y))
            y += line_h

            level = getattr(player, "level", 1)
            level_text = self.small_font.render(f"Level: {level}", True, (200, 200, 255))
            self.screen.blit(level_text, (x, y))
            y += line_h

        # Vague
        if battle is not None and hasattr(battle, "wave"):
            wave_text = self.small_font.render(f"Wave: {battle.wave}", True, (255, 255, 180))
            self.screen.blit(wave_text, (x, y))

        # Equipment display
        self.equip_buttons = []
        y += line_h
        wep_id = player.equipment.get('weapon') if player else None
        arm_id = player.equipment.get('armor') if player else None
        # lookup item data
        wep_item = self.shop_loader.find_item(wep_id) if getattr(self, 'shop_loader', None) and wep_id else None
        arm_item = self.shop_loader.find_item(arm_id) if getattr(self, 'shop_loader', None) and arm_id else None
        wep_name = wep_item.get('name') if wep_item else (wep_id or 'None')
        arm_name = arm_item.get('name') if arm_item else (arm_id or 'None')
        wep_text = self.small_font.render(f"Weapon: {wep_name}", True, (220, 220, 220))
        arm_text = self.small_font.render(f"Armor: {arm_name}", True, (220, 220, 220))
        self.screen.blit(wep_text, (x, y))

        # unequip button for weapon
        uw_rect = pygame.Rect(x + 200, y - 4, 80, 24)
        pygame.draw.rect(self.screen, (180, 80, 80), uw_rect, border_radius=4)
        uw_t = self.small_font.render("Unequip", True, (0, 0, 0))
        self.screen.blit(uw_t, uw_t.get_rect(center=uw_rect.center))
        self.equip_buttons.append({"rect": uw_rect, "action": (lambda p=player: p.unequip('weapon'))})
        # draw icon if available
        if wep_item and self.assets_path:
            icon_path = self.assets_path / 'images' / 'items' / f"{wep_item.get('id')}.png"
            if icon_path.exists():
                ico = pygame.image.load(str(icon_path)).convert_alpha()
                ico = pygame.transform.smoothscale(ico, (20, 20))
                self.screen.blit(ico, (x + 120, y + 6))
        y += line_h
        self.screen.blit(arm_text, (x, y))
        ua_rect = pygame.Rect(x + 200, y - 4, 80, 24)
        pygame.draw.rect(self.screen, (180, 80, 80), ua_rect, border_radius=4)
        ua_t = self.small_font.render("Unequip", True, (0, 0, 0))
        self.screen.blit(ua_t, ua_t.get_rect(center=ua_rect.center))
        self.equip_buttons.append({"rect": ua_rect, "action": (lambda p=player: p.unequip('armor'))})
        if arm_item and self.assets_path:
            icon_path = self.assets_path / 'images' / 'items' / f"{arm_item.get('id')}.png"
            if icon_path.exists():
                ico = pygame.image.load(str(icon_path)).convert_alpha()
                ico = pygame.transform.smoothscale(ico, (20, 20))
                self.screen.blit(ico, (x + 120, y + 6))

        # Allocation UI (si le joueur a des points non dépensés ou si l'UI est ouverte)
        self.alloc_buttons = []
        if player is not None and (getattr(player, 'unspent_points', 0) > 0 or self.allocation_open):
            y += line_h
            up = getattr(player, 'unspent_points', 0)
            up_text = self.small_font.render(f"Unspent points: {up}", True, (255, 220, 180))
            self.screen.blit(up_text, (x, y))
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

            labels = [("+ATK", "atk"), ("+DEF", "def"), ("+HP", "hp")]
            for i, (lab, st) in enumerate(labels):
                btn_rect = pygame.Rect(bx + i * (btn_w + spacing), by, btn_w, btn_h)
                pygame.draw.rect(self.screen, (80, 160, 80), btn_rect, border_radius=6)
                t = self.small_font.render(lab, True, (0, 0, 0))
                trect = t.get_rect(center=btn_rect.center)
                self.screen.blit(t, trect)
                # store for click handling
                self.alloc_buttons.append({"rect": btn_rect, "label": lab, "action": (lambda s=st: player.spend_point(s))})
            y += btn_h + spacing

        # Inventory button
        inv_btn = pygame.Rect(panel_x + panel_w - 110, panel_y + panel_h - 40, 100, 30)
        pygame.draw.rect(self.screen, (120, 100, 200), inv_btn, border_radius=6)
        inv_t = self.small_font.render("Inventory", True, (255, 255, 255))
        self.screen.blit(inv_t, inv_t.get_rect(center=inv_btn.center))
        # store for clicks
        self.inventory_open_rect = inv_btn

        # If inventory modal open, draw a centered panel with items grid
        self.inventory_buttons = []
        self.inventory_cells = []
        if getattr(self, 'inventory_open', False) and player is not None:
            iw, ih = 480, 320
            sx = (self.screen.get_width() - iw) // 2
            sy = (self.screen.get_height() - ih) // 2
            s = pygame.Surface((iw, ih))
            s.fill((40, 40, 60))
            self.screen.blit(s, (sx, sy))
            title = self.title_font.render("Inventory", True, (255, 255, 255))
            self.screen.blit(title, (sx + 10, sy + 8))

            # build list of items from player.inventory
            items = list(player.inventory.items())  # (id, count)
            # display as grid 6 columns with larger cells
            cols = 6
            cell_w = 80
            cell_h = 80
            pad = 8
            start_x = sx + 12
            start_y = sy + 48
            for idx, (iid, cnt) in enumerate(items):
                cx = start_x + (idx % cols) * (cell_w + pad)
                cy = start_y + (idx // cols) * (cell_h + pad)
                rect = pygame.Rect(cx, cy, cell_w, cell_h)
                pygame.draw.rect(self.screen, (70, 70, 100), rect, border_radius=6)
                # highlight if selected
                if self.inventory_selected == iid:
                    pygame.draw.rect(self.screen, (140, 120, 60), rect, width=3, border_radius=6)
                # try load icon
                item_def = None
                if getattr(self, 'shop_loader', None):
                    item_def = self.shop_loader.find_item(iid)
                name = item_def.get('name') if item_def else iid
                # draw icon centered (fallback to a simple rect + first letter)
                ico_rect = pygame.Rect(cx + 8, cy + 8, cell_w - 16, cell_h - 36)
                if self.assets_path:
                    icon_path = self.assets_path / 'images' / 'items' / f"{iid}.png"
                    if icon_path.exists():
                        ico = pygame.image.load(str(icon_path)).convert_alpha()
                        ico = pygame.transform.smoothscale(ico, (ico_rect.w, ico_rect.h))
                        self.screen.blit(ico, ico_rect)
                    else:
                        pygame.draw.rect(self.screen, (100, 100, 140), ico_rect)
                        lt = self.title_font.render(name[:1], True, (220, 220, 220))
                        self.screen.blit(lt, lt.get_rect(center=ico_rect.center))
                else:
                    pygame.draw.rect(self.screen, (100, 100, 140), ico_rect)
                    lt = self.title_font.render(name[:1], True, (220, 220, 220))
                    self.screen.blit(lt, lt.get_rect(center=ico_rect.center))

                # draw count badge at top-right
                badge_rect = pygame.Rect(cx + cell_w - 26, cy + 6, 20, 16)
                pygame.draw.rect(self.screen, (10, 10, 10), badge_rect, border_radius=4)
                bt = self.small_font.render(str(cnt), True, (255, 255, 255))
                self.screen.blit(bt, bt.get_rect(center=badge_rect.center))

                # draw name below cell, truncated
                name_surface = self.small_font.render(name[:12], True, (200, 200, 200))
                self.screen.blit(name_surface, (cx + 4, cy + cell_h - 22))

                # register cell for clicks
                self.inventory_cells.append({'rect': rect, 'item_id': iid, 'count': cnt, 'def': item_def})

            # After drawing grid, draw action buttons for selected item (if any)
            if self.inventory_selected:
                sel_id = self.inventory_selected
                # find selected cell
                sel = None
                for c in self.inventory_cells:
                    if c['item_id'] == sel_id:
                        sel = c
                        break
                if sel:
                    ax = sx + 12
                    ay = start_y + ((len(items)-1)//cols + 1) * (cell_h + pad) + 10
                    # draw description area
                    desc_rect = pygame.Rect(ax, ay, iw - 24, 60)
                    pygame.draw.rect(self.screen, (30, 30, 50), desc_rect, border_radius=6)
                    desc = sel['def'].get('description', '') if sel.get('def') else ''
                    dsurf = self.small_font.render(desc[:60], True, (200, 200, 200))
                    self.screen.blit(dsurf, (ax + 8, ay + 8))

                    # Equip or Use buttons at right side
                    btn_w = 100
                    btn_h = 32
                    bx = sx + iw - btn_w - 12
                    by = ay + 14
                    if sel.get('def') and sel['def'].get('type') in ('weapon', 'armor'):
                        brect = pygame.Rect(bx, by, btn_w, btn_h)
                        pygame.draw.rect(self.screen, (100, 180, 100), brect, border_radius=6)
                        bt = self.small_font.render('Equip', True, (0, 0, 0))
                        self.screen.blit(bt, bt.get_rect(center=brect.center))
                        def make_equip(iid=sel['item_id']):
                            def act():
                                if player.equip_item_by_id(iid):
                                    player.remove_item(iid, 1)
                                    self.inventory_selected = None
                            return act
                        self.inventory_buttons.append({'rect': brect, 'action': make_equip()})
                    elif sel.get('def') and sel['def'].get('type') == 'consumable':
                        brect = pygame.Rect(bx, by, btn_w, btn_h)
                        pygame.draw.rect(self.screen, (180, 140, 60), brect, border_radius=6)
                        bt = self.small_font.render('Use', True, (0, 0, 0))
                        self.screen.blit(bt, bt.get_rect(center=brect.center))
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
                        self.inventory_buttons.append({'rect': brect, 'action': make_use()})

            # close button
            close_rect = pygame.Rect(sx + iw - 90, sy + ih - 36, 80, 28)
            pygame.draw.rect(self.screen, (180, 80, 80), close_rect)
            ct = self.small_font.render('Close', True, (0, 0, 0))
            self.screen.blit(ct, ct.get_rect(center=close_rect.center))
            self.inventory_buttons.append({'rect': close_rect, 'action': (lambda: setattr(self, 'inventory_open', False))})