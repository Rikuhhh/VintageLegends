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
        # inventory modal
        self.inventory_open = False
        self.inventory_buttons = []
        self.inventory_cells = []
        self.inventory_selected = None
        # stats modal
        self.stats_open = False
        self.stats_buttons = []
        self.stats_open_rect = None
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
            # stats open/close button
            if getattr(self, 'stats_open_rect', None) and self.stats_open_rect.collidepoint(event.pos):
                self.stats_open = not self.stats_open
                return
            # stats modal buttons (e.g., close)
            for btn in getattr(self, 'stats_buttons', []):
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return

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
        # larger panel to avoid content overlap
        panel_w = 420
        panel_h = 320
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
        # Weapon line
        self._blit_text_outlined(self.screen, self.small_font, f"Weapon: {wep_name}", (x, y), fg=(220,220,220), outline=(0,0,0), outline_width=2)

        # unequip button for weapon
        uw_rect = pygame.Rect(x + 200, y - 4, 80, 24)
        pygame.draw.rect(self.screen, (180, 80, 80), uw_rect, border_radius=4)
        # unequip button label (no outline for black text on light button)
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

        # Armor line
        self._blit_text_outlined(self.screen, self.small_font, f"Armor: {arm_name}", (x, y), fg=(220,220,220), outline=(0,0,0), outline_width=2)
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

            labels = [("+ATK", "atk"), ("+DEF", "def"), ("+HP", "hp")]
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

        # Inventory button and Stats button next to each other
        inv_btn = pygame.Rect(panel_x + panel_w - 220, panel_y + panel_h - 48, 100, 36)
        stats_btn = pygame.Rect(panel_x + panel_w - 110, panel_y + panel_h - 48, 100, 36)
        pygame.draw.rect(self.screen, (120, 100, 200), inv_btn, border_radius=8)
        pygame.draw.rect(self.screen, (120, 180, 120), stats_btn, border_radius=8)
        self._blit_text_outlined(self.screen, self.small_font, "Inventory", inv_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        self._blit_text_outlined(self.screen, self.small_font, "Stats", stats_btn.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)
        # store for clicks
        self.inventory_open_rect = inv_btn
        self.stats_open_rect = stats_btn

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
            self._blit_text_outlined(self.screen, self.title_font, "Inventory", (sx + 10, sy + 8), fg=(255,255,255), outline=(0,0,0), outline_width=2)

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
                # count badge text with outline for readability
                self._blit_text_outlined(self.screen, self.small_font, str(cnt), badge_rect.center, fg=(255,255,255), outline=(0,0,0), outline_width=2, center=True)

                # draw name below cell, truncated
                self._blit_text_outlined(self.screen, self.small_font, name[:12], (cx + 4, cy + cell_h - 22), fg=(200,200,200), outline=(0,0,0), outline_width=1)

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
                    dsurf = desc[:60]
                    self._blit_text_outlined(self.screen, self.small_font, dsurf, (ax + 8, ay + 8), fg=(200,200,200), outline=(0,0,0), outline_width=1)

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
        # Stats modal
        if getattr(self, 'stats_open', False) and player is not None:
            sw, sh = 420, 320
            sx = (self.screen.get_width() - sw) // 2
            sy = (self.screen.get_height() - sh) // 2
            s = pygame.Surface((sw, sh))
            s.fill((30, 30, 40))
            self.screen.blit(s, (sx, sy))
            # title
            self._blit_text_outlined(self.screen, self.title_font, "Player Stats", (sx + 14, sy + 8), fg=(255,255,255), outline=(0,0,0), outline_width=2)
            # list stats
            stats_x = sx + 16
            stats_y = sy + 48
            stat_lines = [
                f"Name: {getattr(player, 'name', 'Player')}",
                f"Level: {getattr(player, 'level', 1)}",
                f"XP: {getattr(player, 'xp', 0)}",
                f"HP: {player.hp}/{player.max_hp}",
                f"ATK: {player.atk}",
                f"DEF: {player.defense}",
                f"Gold: {player.gold}",
                # Crit stats
                f"Crit Chance: {int(getattr(player, 'critchance', 0.0) * 100)}%",
                f"Crit Damage: {round(getattr(player, 'critdamage', 1.5), 2)}x",
            ]
            sy_off = 0
            for line in stat_lines:
                self._blit_text_outlined(self.screen, self.small_font, line, (stats_x, stats_y + sy_off), fg=(220,220,220), outline=(0,0,0), outline_width=1)
                sy_off += 28
            # close button
            crect = pygame.Rect(sx + sw - 92, sy + sh - 44, 80, 32)
            pygame.draw.rect(self.screen, (180, 80, 80), crect, border_radius=6)
            ct = self.small_font.render('Close', True, (0,0,0))
            self.screen.blit(ct, ct.get_rect(center=crect.center))
            self.stats_buttons = [{'rect': crect, 'action': (lambda: setattr(self, 'stats_open', False))}]

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