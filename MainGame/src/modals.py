import pygame
import sys
import time
import json
from pathlib import Path

# Note: functions expect certain variables/objects to be passed in (player, battle, ui, shop, save_manager, background, screen, clock, ASSETS_PATH, DATA_PATH, Enemy, PlayerClass)
# This keeps the module stateless and testable.


def handle_console_event(ev, console_state, player, battle, save_manager):
    """Handle console input events.
    console_state is a dict {'open': bool, 'text': str}
    Returns True if the event was consumed.
    """
    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_BACKQUOTE:
        console_state['open'] = not console_state.get('open', False)
        if console_state['open']:
            console_state['text'] = ''
        return True
    if not console_state.get('open', False):
        return False
    if ev.type == pygame.KEYDOWN:
        if ev.key == pygame.K_RETURN:
            cmd = console_state.get('text', '').strip()
            if cmd == 'reset_challenges':
                try:
                    player.challenge_coins = 0
                    player.permanent_upgrades = {}
                    player._recalc_stats()
                    save_manager.save(player)
                    try:
                        battle.damage_events.append({'type': 'note', 'msg': 'Challenges reset', 'time': time.time()})
                    except Exception:
                        pass
                except Exception as e:
                    print('reset_challenges failed', e)
            console_state['open'] = False
            console_state['text'] = ''
        elif ev.key == pygame.K_BACKSPACE:
            console_state['text'] = console_state.get('text', '')[:-1]
        else:
            ch = getattr(ev, 'unicode', '')
            if ch:
                console_state['text'] = console_state.get('text', '') + ch
    return True


def show_shop_modal(screen, background, ui, player, battle, offers, ASSETS_PATH, clock, save_manager=None):
    sf = pygame.font.Font(None, 36)
    panel_x, panel_y, panel_w, panel_h = 180, 100, 520, 360
    close_rect = pygame.Rect(panel_x + panel_w - 70, panel_y + 10, 60, 30)
    shop_open = True
    while shop_open:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if close_rect.collidepoint((mx, my)):
                    shop_open = False
                for idx, item in enumerate(offers):
                    by = 150 + idx * 64
                    buy_rect = pygame.Rect(panel_x + 340, by, 80, 48)
                    if buy_rect.collidepoint((mx, my)):
                        cost = item.get('_final_cost', item.get('cost', 0))
                        if player.gold >= cost:
                            player.gold -= cost
                            itm = {k: v for k, v in item.items() if not k.startswith('_')}
                            player.add_item(itm, auto_equip=False)
                        else:
                            print('Not enough gold')
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                shop_open = False
        screen.blit(background, (0, 0))
        ui.draw(player, battle)
        pygame.draw.rect(screen, (30, 30, 40), (panel_x, panel_y, panel_w, panel_h))
        title = sf.render(f'Shop - Wave {battle.wave}', True, (255,255,255))
        screen.blit(title, (panel_x + 20, panel_y + 10))
        pygame.draw.rect(screen, (200,80,80), close_rect, border_radius=6)
        cr = sf.render('Close', True, (0,0,0))
        screen.blit(cr, cr.get_rect(center=close_rect.center))
        for idx, item in enumerate(offers):
            by = 150 + idx * 64
            icon_path = ASSETS_PATH / 'images' / 'items' / f"{item.get('id')}.png"
            if icon_path.exists():
                ico = pygame.image.load(str(icon_path)).convert_alpha()
                ico = pygame.transform.smoothscale(ico, (48,48))
                screen.blit(ico, (panel_x + 20, by))
            else:
                t = sf.render(item.get('name', item.get('id')), True, (220,220,220))
                screen.blit(t, (panel_x + 80, by + 8))
            price = item.get('_final_cost', item.get('cost', 0))
            p = sf.render(f"{price}g", True, (255,215,0))
            name = item.get('name', item.get('id'))
            name_x = panel_x + 80
            price_x = panel_x + 240
            max_name_w = max(16, price_x - name_x - 12)
            rendered = sf.render(name, True, (220,220,220))
            if rendered.get_width() > max_name_w:
                truncated = name
                while truncated and sf.render(truncated + '...', True, (0,0,0)).get_width() > max_name_w:
                    truncated = truncated[:-1]
                name = (truncated + '...') if truncated else name[:8]
            n = sf.render(name, True, (220,220,220))
            screen.blit(n, (name_x, by + 8))
            screen.blit(p, (price_x, by + 8))
            buy_rect = pygame.Rect(panel_x + 340, by, 80, 48)
            pygame.draw.rect(screen, (80,160,80), buy_rect, border_radius=6)
            bt = sf.render('Buy', True, (0,0,0))
            screen.blit(bt, bt.get_rect(center=buy_rect.center))
        pygame.display.flip()
        clock.tick(30)


def show_challenge_shop_modal(screen, background, ui, player, battle, DATA_PATH, clock, save_manager):
    up_defs = (DATA_PATH / 'upgrades.json')
    try:
        with open(up_defs, 'r', encoding='utf-8') as f:
            data = json.load(f)
        up_defs = data.get('upgrades', [])
    except Exception:
        up_defs = []
    mw, mh = 560, 420
    mx0 = screen.get_width()//2 - mw//2
    my0 = screen.get_height()//2 - mh//2
    close_c_rect = pygame.Rect(mx0 + mw - 90, my0 + mh - 44, 80, 32)
    open_challenge_shop = True
    while open_challenge_shop:
        for ce in pygame.event.get():
            if ce.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ce.type == pygame.MOUSEBUTTONDOWN and ce.button == 1:
                mx2, my2 = ce.pos
                if close_c_rect.collidepoint((mx2, my2)):
                    open_challenge_shop = False
                    break
                for i, u in enumerate(up_defs):
                    uy = my0 + 100 + i * 56
                    buy_rect = pygame.Rect(mx0 + 420, uy, 100, 40)
                    if buy_rect.collidepoint((mx2, my2)):
                        cost = int(u.get('cost', 1))
                        uid = u.get('id')
                        cur = player.permanent_upgrades.get(uid, 0)
                        if player.challenge_coins >= cost and cur < int(u.get('max_level', 99)):
                            player.challenge_coins -= cost
                            player.permanent_upgrades[uid] = cur + 1
                            player._recalc_stats()
                            try:
                                save_manager.save(player)
                            except Exception:
                                pass
        screen.blit(background, (0,0))
        ui.draw(player, battle)
        pygame.draw.rect(screen, (30,30,40), (mx0, my0, mw, mh))
        title = pygame.font.Font(None, 40).render('Challenge Shop', True, (255,255,255))
        screen.blit(title, (mx0 + 16, my0 + 12))
        coin_t = pygame.font.Font(None, 28).render(f'Coins: {player.challenge_coins}', True, (255,215,0))
        screen.blit(coin_t, (mx0 + 16, my0 + 56))
        for i, u in enumerate(up_defs):
            uy = my0 + 100 + i * 56
            name = u.get('name')
            cur = player.permanent_upgrades.get(u.get('id'), 0)
            lvl = pygame.font.Font(None, 28).render(f"{name} (Lv {cur})", True, (220,220,220))
            screen.blit(lvl, (mx0 + 16, uy))
            cost = int(u.get('cost', 1))
            cost_t = pygame.font.Font(None, 24).render(f"{cost}c", True, (255,215,0))
            screen.blit(cost_t, (mx0 + 360, uy))
            buy_rect = pygame.Rect(mx0 + 420, uy, 100, 40)
            pygame.draw.rect(screen, (80,160,80), buy_rect, border_radius=6)
            bt = pygame.font.Font(None, 28).render('Buy', True, (0,0,0))
            screen.blit(bt, bt.get_rect(center=buy_rect.center))
        pygame.draw.rect(screen, (200,80,80), close_c_rect, border_radius=6)
        ct = pygame.font.Font(None, 28).render('Close', True, (0,0,0))
        screen.blit(ct, ct.get_rect(center=close_c_rect.center))
        pygame.display.flip()
        clock.tick(30)


def show_game_over_modal(screen, background, ui, player, battle, clock, show_challenge_fn):
    modal_font = pygame.font.Font(None, 96)
    small_font = pygame.font.Font(None, 36)
    btn_w, btn_h = 160, 48
    spacing = 20
    total_w = btn_w * 2 + spacing
    bx = screen.get_width() // 2 - total_w // 2
    by = screen.get_height() // 2 + 40
    retry_rect = pygame.Rect(bx, by, btn_w, btn_h)
    quit_rect = pygame.Rect(bx + btn_w + spacing, by, btn_w, btn_h)
    cs_rect = pygame.Rect(bx - btn_w - spacing, by, btn_w, btn_h)
    game_over = True
    while game_over:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if cs_rect.collidepoint((mx, my)):
                    show_challenge_fn()
                    continue
                if retry_rect.collidepoint((mx, my)):
                    try:
                        player.highest_wave = max(getattr(player, 'highest_wave', 0), battle.wave)
                        # save_manager handled by caller if needed
                    except Exception:
                        pass
                    return 'retry'
                if quit_rect.collidepoint((mx, my)):
                    try:
                        player.highest_wave = max(getattr(player, 'highest_wave', 0), battle.wave)
                    except Exception:
                        pass
                    return 'quit'
        screen.blit(background, (0, 0))
        if hasattr(player, 'sprite') and player.sprite:
            screen.blit(player.sprite, (100, 500))
        ui.draw(player, battle)
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))
        go_text = modal_font.render('Game Over', True, (255,50,50))
        go_rect = go_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 80))
        screen.blit(go_text, go_rect)
        wave_text = small_font.render(f'Highest Wave: {battle.wave}', True, (255,255,255))
        wave_rect = wave_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 20))
        screen.blit(wave_text, wave_rect)
        pygame.draw.rect(screen, (120,100,200), cs_rect, border_radius=8)
        cs_t = small_font.render('Challenge Shop', True, (255,255,255))
        screen.blit(cs_t, cs_t.get_rect(center=cs_rect.center))
        pygame.draw.rect(screen, (80,160,80), retry_rect, border_radius=8)
        pygame.draw.rect(screen, (200,80,80), quit_rect, border_radius=8)
        rt = small_font.render('Retry', True, (0,0,0))
        qt = small_font.render('Quit', True, (0,0,0))
        screen.blit(rt, rt.get_rect(center=retry_rect.center))
        screen.blit(qt, qt.get_rect(center=quit_rect.center))
        pygame.display.flip()
        clock.tick(30)


def show_class_select_modal(screen, background, ui, data_path, clock):
    """Simple modal to choose a starting class from characters.json.
    Returns the chosen character id (e.g., 'mage') or None for default.
    """
    chars_file = Path(data_path) / 'characters.json'
    try:
        with open(chars_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chars = data.get('characters', [])
    except Exception:
        chars = []

    mw, mh = 640, 240
    mx0 = screen.get_width()//2 - mw//2
    my0 = screen.get_height()//2 - mh//2
    btns = []
    font = pygame.font.Font(None, 28)
    for i, c in enumerate(chars):
        bx = mx0 + 24 + i * 200
        by = my0 + 100
        rect = pygame.Rect(bx, by, 160, 48)
        btns.append((rect, c.get('id')))

    selecting = True
    while selecting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for rect, cid in btns:
                    if rect.collidepoint((mx, my)):
                        return cid
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return None

        screen.blit(background, (0,0))
        ui.draw(None, None)  # draw base UI if needed
        pygame.draw.rect(screen, (20,20,30), (mx0, my0, mw, mh))
        title = pygame.font.Font(None, 40).render('Choose your class', True, (255,255,255))
        screen.blit(title, (mx0 + 20, my0 + 8))
        for rect, cid in btns:
            pygame.draw.rect(screen, (80,120,160), rect, border_radius=6)
            lbl = font.render(cid.capitalize(), True, (255,255,255))
            screen.blit(lbl, lbl.get_rect(center=rect.center))

        pygame.display.flip()
        clock.tick(30)


def show_start_menu_modal(screen, background, ui, save_exists, clock):
    """If a save exists, ask the player whether to Continue or start New Game.
    Returns 'continue' or 'new' or None if cancelled.
    """
    mw, mh = 420, 160
    mx0 = screen.get_width()//2 - mw//2
    my0 = screen.get_height()//2 - mh//2
    font = pygame.font.Font(None, 28)
    cont_rect = pygame.Rect(mx0 + 40, my0 + 80, 140, 44)
    new_rect = pygame.Rect(mx0 + 220, my0 + 80, 140, 44)

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if cont_rect.collidepoint((mx, my)):
                    return 'continue'
                if new_rect.collidepoint((mx, my)):
                    return 'new'
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return None

        screen.blit(background, (0,0))
        ui.draw(None, None)
        pygame.draw.rect(screen, (30,30,40), (mx0, my0, mw, mh))
        title = pygame.font.Font(None, 36).render('Save found', True, (255,255,255))
        screen.blit(title, (mx0 + 16, my0 + 12))
        txt = font.render('A saved game was detected. Continue or start a new game?', True, (220,220,220))
        screen.blit(txt, (mx0 + 16, my0 + 48))
        pygame.draw.rect(screen, (80,160,80), cont_rect, border_radius=6)
        pygame.draw.rect(screen, (80,120,200), new_rect, border_radius=6)
        screen.blit(font.render('Continue', True, (0,0,0)), font.render('Continue', True, (0,0,0)).get_rect(center=cont_rect.center))
        screen.blit(font.render('New Game', True, (0,0,0)), font.render('New Game', True, (0,0,0)).get_rect(center=new_rect.center))
        pygame.display.flip()
        clock.tick(30)
