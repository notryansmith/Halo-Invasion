import pygame
import sys
import random
import math

# ----------------------------------------------------
# INITIAL SETUP
# ----------------------------------------------------
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Halo: Invasion")
clock = pygame.time.Clock()

# ----------------------------------------------------
# AUDIO LOADING
# ----------------------------------------------------
pygame.mixer.music.set_volume(0.05)
click_sound = pygame.mixer.Sound("play_button_sound.mp3")

gun_loop = pygame.mixer.Sound("machinegunsound.mp3")
gun_loop.set_volume(0.1)
gun_channel = pygame.mixer.Channel(1)
shoot_sound_playing = False

banshee_fire_sound = pygame.mixer.Sound("banshee_gun_sound.mp3")
banshee_fire_sound.set_volume(0.1)

banshee_death_sound = pygame.mixer.Sound("banshee_explosion_sound.mp3")
banshee_death_sound.set_volume(0.2)

# Music Helper Functions
def play_menu_music():
    pygame.mixer.music.load("Halo Theme Song Original.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
    
def play_game_music():
    pygame.mixer.music.load("game_music.mp3")
    pygame.mixer.music.set_volume(0.05)
    pygame.mixer.music.play(-1)
    
def stop_music(fadeout_ms=0):
    if fadeout_ms > 0:
        pygame.mixer.music.fadeout(fadeout_ms)
    else:
        pygame.mixer.music.stop()

# ----------------------------------------------------
# VISUAL ASSETS
# ----------------------------------------------------
background_menu = pygame.image.load("main_menu_art.jpg").convert()
background_game = pygame.image.load("game_background_art.jpg").convert()
bg_y1 = 0
bg_y2 = -SCREEN_HEIGHT
bg_scroll_speed = 10

font = pygame.font.Font("Halo.ttf", 85)
title_font = pygame.font.Font("Halo.ttf", 120)

title_text = title_font.render("Halo: Invasion", True, (255, 255, 255))
title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
title_shadow = title_font.render("Halo: Invasion", True, (0, 0, 0))
title_shadow_rect = title_shadow.get_rect(center=(SCREEN_WIDTH // 2 + 4, 154))

play_text_normal = font.render("PLAY", True, (255, 255, 255))
play_text_hover = font.render("PLAY", True, (0, 140, 255))
play_shadow_normal = font.render("PLAY", True, (0, 0, 0))
play_shadow_hover = font.render("PLAY", True, (0, 140, 255))
play_rect = play_text_normal.get_rect(center=(SCREEN_WIDTH // 2, 550))

fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
fade_surface.fill((0, 0, 0))

# ----------------------------------------------------
# BULLET CLASSES
# ----------------------------------------------------
class Bullet:
    def __init__(self, x, y):
        self.image = pygame.Surface((2, 4))
        self.image.fill((255, 255, 180))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -50

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def off_screen(self):
        return self.rect.bottom < 0

class EnemyBullet:
    def __init__(self, x, y):
        self.image = pygame.Surface((2,12))
        self.image.fill((0, 200, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 8
        
    def update(self):
        self.rect.y += self.speed
        
    def off_screen(self):
        return self.rect.top > SCREEN_HEIGHT
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)

# ----------------------------------------------------
# PLAYER CLASS
# ----------------------------------------------------
class Player:
    def __init__(self):
        self.center_image = pygame.image.load("new_player.png").convert_alpha()
        self.left_image = pygame.image.load("new_player_turnleft.png").convert_alpha()
        self.right_image = pygame.image.load("new_player_turnright.png").convert_alpha()

        self.center_image = self.scale_image(self.center_image, 90)
        self.left_image = self.scale_image(self.left_image, 80)
        self.right_image = self.scale_image(self.right_image, 80)

        self.image = self.center_image
        self.rect = self.image.get_rect()
        self.fixed_y = SCREEN_HEIGHT - 100
        self.rect.center = (SCREEN_WIDTH // 2, self.fixed_y)

        self.speed = 8
        self.shoot_cooldown = 250
        self.last_shot = 0

        self.max_health = 6
        self.health = self.max_health

        # New shooting cooldown variables
        self.shoot_max_time = 3000   # 3 seconds of continuous fire
        self.cooldown_time = 1000    # 1 second cooldown
        self.shoot_timer = 0
        self.cooldown_timer = 0
        self.can_shoot = True

    def scale_image(self, image, desired_width):
        original_width = image.get_width()
        original_height = image.get_height()
        scale_factor = desired_width / original_width
        new_height = int(original_height * scale_factor)
        return pygame.transform.scale(image, (desired_width, new_height))

    def update(self):
        keys = pygame.key.get_pressed()
        moving_left = moving_right = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
            moving_left = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
            moving_right = True

        if moving_left:
            self.image = self.left_image
        elif moving_right:
            self.image = self.right_image
        else:
            self.image = self.center_image

        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, SCREEN_WIDTH)
        self.rect.centery = self.fixed_y

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        bar_width = 200
        bar_height = 20
        x = 20
        y = 20
        fill = (self.health / self.max_health) * bar_width
        pygame.draw.rect(surface, (255,0,0), (x, y, bar_width, bar_height))
        pygame.draw.rect(surface, (0,255,0), (x, y, fill, bar_height))
        pygame.draw.rect(surface, (0,0,0), (x, y, bar_width, bar_height), 2)

    def shoot(self, bullets):
        if not self.can_shoot:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot < self.shoot_cooldown:
            return
        self.last_shot = current_time
        self.shoot_timer += self.shoot_cooldown

        left_x = self.rect.centerx - 10
        right_x = self.rect.centerx + 10
        y = self.rect.top
        bullets.append(Bullet(left_x, y))
        bullets.append(Bullet(right_x, y))

        if self.shoot_timer >= self.shoot_max_time:
            self.can_shoot = False
            self.cooldown_timer = 0
            self.shoot_timer = 0

# ----------------------------------------------------
# BANSHEE CLASSES
# ----------------------------------------------------
class Banshee:
    def __init__(self, start_x, scale=150, health=3):
        self.center_image = pygame.image.load("banshee.png").convert_alpha()
        self.left_image = pygame.image.load("banshee_turnleft.png").convert_alpha()
        self.right_image = pygame.image.load("banshee_turnright.png").convert_alpha()
        
        self.center_image = self.scale_image(self.center_image, scale)
        self.left_image = self.scale_image(self.left_image, scale)
        self.right_image = self.scale_image(self.right_image, scale)
        
        self.image = self.center_image
        self.rect = self.image.get_rect(center=(start_x, -self.center_image.get_height()))
        
        self.y_speed = 2
        self.sway_amplitude = 150
        self.sway_speed = 0.03
        self.start_x = start_x
        self.time = 0
        self.health = health

        self.burst_size = 3
        self.burst_interval = 120
        self.burst_cooldown = random.randint(900, 1500)
        self.last_shot = 0
        self.in_burst = False
        self.bullets_fired_in_burst = 0

    def scale_image(self, image, desired_width):
        w = image.get_width()
        h = image.get_height()
        scale_factor = desired_width / w
        new_height = int(h * scale_factor)
        return pygame.transform.smoothscale(image, (desired_width, new_height))
    
    def update(self):
        self.rect.y += self.y_speed
        self.rect.centerx = self.start_x + int(self.sway_amplitude * math.sin(self.time))
        self.time += self.sway_speed

        if math.cos(self.time) < 0:
            self.image = self.right_image
        else:
            self.image = self.left_image

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def has_hit_player(self, player_rect):
        return self.rect.colliderect(player_rect)
    
    def take_damage(self, amount=1):
        self.health -= amount
        return self.health <= 0
    
    def shoot(self, enemy_bullets):
        current_time = pygame.time.get_ticks()
        if not self.in_burst:
            if current_time - self.last_shot >= self.burst_cooldown:
                self.in_burst = True
                self.bullets_fired_in_burst = 0
                self.last_shot = current_time
            else:
                return
        if current_time - self.last_shot >= self.burst_interval:
            left_x = self.rect.centerx - 20
            right_x = self.rect.centerx + 20
            y = self.rect.bottom
            enemy_bullets.append(EnemyBullet(left_x, y))
            enemy_bullets.append(EnemyBullet(right_x, y))
            banshee_fire_sound.play()
            self.bullets_fired_in_burst += 1
            self.last_shot = current_time
            if self.bullets_fired_in_burst >= self.burst_size:
                self.in_burst = False
                self.burst_cooldown = random.randint(900, 1500)
                banshee_fire_sound.stop()

class ZigZagBanshee(Banshee):
    def __init__(self, start_x, scale=150):
        super().__init__(start_x, scale)
        self.direction = 1
        self.horizontal_speed = 3
    
    def update(self):
        self.rect.y += self.y_speed
        self.rect.x += self.direction * self.horizontal_speed
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.direction *= -1
        if self.direction < 0:
            self.image = self.right_image
        else:
            self.image = self.left_image

# ----------------------------------------------------
# MAIN MENU LOOP
# ----------------------------------------------------
def main_menu():
    play_menu_music()
    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    click_sound.play()
                    stop_music(fadeout_ms=1500)
                    play_game_music()

                    for alpha in range(0, 255, 5):
                        screen.blit(background_menu, (0, 0))
                        screen.blit(title_shadow, title_shadow_rect)
                        screen.blit(title_text, title_rect)
                        screen.blit(play_shadow_normal, (play_rect.x + 3, play_rect.y + 3))
                        screen.blit(play_text_normal, play_rect)
                        fade_surface.set_alpha(alpha)
                        screen.blit(fade_surface, (0, 0))
                        pygame.display.flip()
                        clock.tick(60)

                    menu_running = False

        screen.blit(background_menu, (0, 0))
        screen.blit(title_shadow, title_shadow_rect)
        screen.blit(title_text, title_rect)
        mouse_pos = pygame.mouse.get_pos()
        if play_rect.collidepoint(mouse_pos):
            screen.blit(play_shadow_hover, (play_rect.x + 3, play_rect.y + 3))
            screen.blit(play_text_hover, play_rect)
        else:
            screen.blit(play_shadow_normal, (play_rect.x + 3, play_rect.y + 3))
            screen.blit(play_text_normal, play_rect)

        pygame.display.flip()
        clock.tick(60)

# ----------------------------------------------------
# GAME OVER SCREEN
# ----------------------------------------------------
def game_over_screen(score):
    font_small = pygame.font.Font("Halo.ttf", 60)
    restart_text = font_small.render("RESTART", True, (255,255,255))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, 400))
    exit_text = font_small.render("EXIT", True, (255,255,255))
    exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH//2, 500))

    running = True
    while running:
        screen.fill((0,0,0))
        title = font.render(f"You destroyed {score} banshees!", True, (255,255,255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 200))
        screen.blit(title, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        if restart_rect.collidepoint(mouse_pos):
            screen.blit(restart_text, restart_rect)
        else:
            screen.blit(restart_text, restart_rect)
        if exit_rect.collidepoint(mouse_pos):
            screen.blit(exit_text, exit_rect)
        else:
            screen.blit(exit_text, exit_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_rect.collidepoint(event.pos):
                    click_sound.play()
                    return True
                if exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(60)

# ----------------------------------------------------
# GAME LOOP
# ----------------------------------------------------
def game_loop():
    global bg_y1, bg_y2, shoot_sound_playing
    player = Player()
    bullets = []
    banshees = []
    enemy_bullets = []
    banshee_spawn_delay = 2000
    last_banshee_spawn = 0
    score = 0

    game_running = True
    while game_running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Background scroll
        bg_y1 += bg_scroll_speed
        bg_y2 += bg_scroll_speed
        if bg_y1 >= SCREEN_HEIGHT:
            bg_y1 = -SCREEN_HEIGHT
        if bg_y2 >= SCREEN_HEIGHT:
            bg_y2 = -SCREEN_HEIGHT

        keys = pygame.key.get_pressed()
        shooting = keys[pygame.K_SPACE]
        current_time = pygame.time.get_ticks()

        # Spawn banshees
        if current_time - last_banshee_spawn > banshee_spawn_delay:
            spawn_x = random.randint(100, SCREEN_WIDTH - 100)
            new_banshee = Banshee(start_x=spawn_x, scale=80) if random.random() < 0.5 else ZigZagBanshee(start_x=spawn_x, scale=80)
            banshees.append(new_banshee)
            banshee_spawn_delay = random.randint(1000, 2500)
            last_banshee_spawn = current_time

        # Shooting logic with cooldown & sound
        if shooting and player.can_shoot:
            player.shoot(bullets)
            if not shoot_sound_playing:
                gun_channel.play(gun_loop, loops=-1)
                shoot_sound_playing = True
        elif not shooting or not player.can_shoot:
            if shoot_sound_playing:
                gun_channel.stop()
                shoot_sound_playing = False

        # Update cooldown timer
        if not player.can_shoot:
            player.cooldown_timer += dt
            if player.cooldown_timer >= player.cooldown_time:
                player.can_shoot = True
                player.cooldown_timer = 0

        # Update bullets
        for bullet in bullets[:]:
            bullet.update()
            for banshee in banshees[:]:
                if bullet.rect.colliderect(banshee.rect):
                    bullets.remove(bullet)
                    if banshee.take_damage():
                        banshee_death_sound.play()
                        banshees.remove(banshee)
                        score += 1
                    break
            else:
                if bullet.off_screen():
                    bullets.remove(bullet)

        # Update player
        player.update()

        # Update enemy bullets
        for e_bullet in enemy_bullets[:]:
            e_bullet.update()
            if e_bullet.rect.colliderect(player.rect):
                player.health -= 1
                enemy_bullets.remove(e_bullet)
                if player.health <= 0:
                    gun_channel.stop()
                    shoot_sound_playing = False
                    game_running = False
                    break
            elif e_bullet.off_screen():
                enemy_bullets.remove(e_bullet)

        # Update banshees
        for banshee in banshees[:]:
            banshee.update()
            banshee.shoot(enemy_bullets)
            if banshee.rect.top > SCREEN_HEIGHT + 200:
                banshees.remove(banshee)
                continue
            if banshee.has_hit_player(player.rect):
                player.health = 0
                gun_channel.stop()
                shoot_sound_playing = False
                game_running = False
                break

        # Draw everything
        screen.blit(background_game, (0, bg_y1))
        screen.blit(background_game, (0, bg_y2))
        for bullet in bullets:
            bullet.draw(screen)
        for e_bullet in enemy_bullets:
            e_bullet.draw(screen)
        for banshee in banshees:
            banshee.draw(screen)
        player.draw(screen)

        # Draw score
        score_font = pygame.font.Font("Halo.ttf", 40)  # smaller size than the main font
        score_text = score_font.render(f"Banshees destroyed: {score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 50))
        pygame.display.flip()

    # Game over screen
    restart = game_over_screen(score)
    if restart:
        game_loop()

# ----------------------------------------------------
# RUN GAME
# ----------------------------------------------------
main_menu()
game_loop()

