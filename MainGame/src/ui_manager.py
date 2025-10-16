# src/ui_manager.py
import pygame

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []

    def set_actions(self, battle):
        screen_width, screen_height = self.screen.get_size()
        self.buttons = [
            {
                "rect": pygame.Rect(screen_width - 300, screen_height - 100, 200, 60),
                "label": "⚔️ Attaquer",
                "action": battle.player_attack,
            },
        ]


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()

    def update(self, player, battle):
        pass  # tu peux afficher les stats ici si tu veux

    def draw(self, player=None, battle=None):
    # Boutons
        for btn in self.buttons:
            pygame.draw.rect(self.screen, (100, 100, 250), btn["rect"], border_radius=8)
            font = pygame.font.Font(None, 36)
            text = font.render(btn["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)

        # Affichage des infos joueur / ennemi
        font = pygame.font.Font(None, 28)
        if player is not None:
            self.screen.blit(font.render(f"HP Joueur: {player.hp}/{player.max_hp}", True, (255, 255, 255)), (30, 30))
        if battle is not None and hasattr(battle, "enemy") and battle.enemy:
            self.screen.blit(font.render(f"Ennemi: {battle.enemy.name}", True, (255, 200, 200)), (30, 60))
            self.screen.blit(font.render(f"HP Ennemi: {battle.enemy.hp}/{battle.enemy.max_hp}", True, (255, 150, 150)), (30, 90))

            # Affichage de la barre de vie du slime (ennemi)
            if battle is not None and hasattr(battle, "enemy") and battle.enemy:
                # Barre de vie
                bar_x, bar_y = 30, 120
                bar_width, bar_height = 200, 20
                hp_ratio = battle.enemy.hp / battle.enemy.max_hp if battle.enemy.max_hp > 0 else 0
                pygame.draw.rect(self.screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))  # fond
                pygame.draw.rect(self.screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))  # hp
                hp_text = font.render(f"Slime HP: {battle.enemy.hp}/{battle.enemy.max_hp}", True, (255, 255, 255))
                self.screen.blit(hp_text, (bar_x + bar_width + 10, bar_y))

            # Affichage des stats joueur
            if player is not None:
                gold_text = font.render(f"Gold: {getattr(player, 'gold', 0)}", True, (255, 215, 0))
                self.screen.blit(gold_text, (30, 150))
                level_text = font.render(f"Level: {getattr(player, 'level', 1)}", True, (200, 200, 255))
                self.screen.blit(level_text, (30, 180))

            # Affichage de la vague
            if battle is not None and hasattr(battle, "wave"):
                wave_text = font.render(f"Wave: {battle.wave}", True, (255, 255, 180))
                self.screen.blit(wave_text, (30, 210))