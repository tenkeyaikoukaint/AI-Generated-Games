import pygame
import sys
import math
import random

# --- 基本設定 ---
VIRTUAL_W, VIRTUAL_H = 320, 180
SCALE = 3
SCREEN_W, SCREEN_H = VIRTUAL_W * SCALE, VIRTUAL_H * SCALE
FPS = 60
GROUND_Y = 152

# カラーパレット（ローレゾ風）
BG_DARK = (16, 18, 28)
BG_MID = (28, 32, 48)
FLOOR_COL = (45, 50, 70)
FLOOR_LINE = (80, 90, 120)
WHITE = (245, 245, 250)
YELLOW = (255, 220, 80)
CYAN = (80, 230, 255)
MAGENTA = (255, 80, 160)
RED = (240, 70, 70)
BLUE = (70, 150, 255)
GREEN = (80, 220, 120)

# --- ドット絵定義 (12x16) ---
# '.'=透明, '1'=メイン色, '2'=暗色, '3'=肌/ライト, '4'=目/アクセント
SPRITE_IDLE = [
    "....1111....",
    "...111111...",
    "...133331...",
    "...134341...",
    "....3333....",
    "...211112...",
    "..21111112..",
    "..21122112..",
    "..3.1111.3..",
    "....1111....",
    "....2222....",
    "...22..22...",
    "...22..22...",
    "...11..11...",
    "..222..222..",
    "............",
]

SPRITE_WALK = [
    "....1111....",
    "...111111...",
    "...133331...",
    "...134341...",
    "....3333....",
    "...211112...",
    "..21111112..",
    "...212212...",
    "...311113...",
    "....1111....",
    "...222222...",
    "..22....22..",
    "..11....11..",
    ".222....222.",
    "............",
    "............",
]


def build_sprite(pattern, palette):
    surf = pygame.Surface((len(pattern[0]), len(pattern)), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            if ch in palette:
                surf.set_at((x, y), palette[ch])
    return surf


class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08
        self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            s = max(1, int(self.size * (self.life / self.max_life)))
            pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), s, s))


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 35

    def update(self):
        self.y -= 0.4
        self.life -= 1

    def draw(self, surf, font):
        if self.life > 0:
            img = font.render(self.text, False, self.color)
            surf.blit(img, (int(self.x - img.get_width() // 2), int(self.y)))


class Bullet:
    def __init__(self, x, y, direction, owner):
        self.x = x
        self.y = y
        self.vx = direction * 5.2
        self.owner = owner
        self.alive = True
        self.radius = 2

    def update(self):
        self.x += self.vx
        if self.x < -10 or self.x > VIRTUAL_W + 10:
            self.alive = False

    def draw(self, surf):
        pygame.draw.rect(surf, YELLOW, (int(self.x - 3), int(self.y - 1), 6, 3))
        pygame.draw.rect(surf, WHITE, (int(self.x - 1), int(self.y - 1), 2, 2))


class Fighter:
    def __init__(self, x, facing, palette, is_cpu=False):
        self.start_x = x
        self.start_facing = facing
        self.palette = palette
        self.is_cpu = is_cpu

        self.sprite_idle = build_sprite(SPRITE_IDLE, palette)
        self.sprite_walk = build_sprite(SPRITE_WALK, palette)
        self.w = 12
        self.h = 16
        self.reset()

    def reset(self):
        self.x = float(self.start_x)
        self.y = float(GROUND_Y - self.h)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = self.start_facing
        self.on_ground = True

        self.hp = 100
        self.max_hp = 100
        self.barrier_energy = 100.0
        self.barrier_active = False
        self.barrier_broken = 0

        self.sword_timer = 0      # 剣攻撃の持続フレーム
        self.sword_cd = 0         # 剣のクールダウン
        self.sword_hit_done = False

        self.gun_timer = 0        # 銃構えモーション
        self.gun_cd = 0           # 銃のクールダウン

        self.hitstun = 0
        self.flash_timer = 0
        self.anim_tick = 0
        self.ai_timer = 0
        self.ai_action = "idle"

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    @property
    def center(self):
        return (self.x + self.w / 2, self.y + self.h / 2)

    @property
    def barrier_radius(self):
        return 14

    def sword_hitbox(self):
        # 剣のリーチ（結界を通過する近接判定）
        reach = 18
        if self.facing == 1:
            return pygame.Rect(int(self.x + self.w - 2), int(self.y + 1), reach, self.h - 2)
        else:
            return pygame.Rect(int(self.x - reach + 2), int(self.y + 1), reach, self.h - 2)

    def start_sword(self):
        if self.sword_cd == 0 and self.hitstun == 0 and not self.barrier_active:
            self.sword_timer = 12
            self.sword_cd = 22
            self.sword_hit_done = False
            self.vx += self.facing * 1.4  # 踏み込み

    def start_gun(self, bullets, particles):
        if self.gun_cd == 0 and self.hitstun == 0 and not self.barrier_active and self.sword_timer == 0:
            self.gun_timer = 10
            self.gun_cd = 28
            bx = self.x + (self.w + 3 if self.facing == 1 else -3)
            by = self.y + 7
            bullets.append(Bullet(bx, by, self.facing, self))
            # マズルフラッシュ
            for _ in range(4):
                particles.append(Particle(
                    bx, by,
                    self.facing * random.uniform(0.5, 2.0),
                    random.uniform(-1.0, 1.0),
                    YELLOW, 8, 2
                ))

    def update(self, opponent, keys, bullets, particles, mode_2p=False):
        self.anim_tick += 1
        if self.sword_timer > 0:
            self.sword_timer -= 1
        if self.sword_cd > 0:
            self.sword_cd -= 1
        if self.gun_timer > 0:
            self.gun_timer -= 1
        if self.gun_cd > 0:
            self.gun_cd -= 1
        if self.hitstun > 0:
            self.hitstun -= 1
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.barrier_broken > 0:
            self.barrier_broken -= 1

        move = 0
        jump = False
        want_barrier = False
        want_sword = False
        want_gun = False

        if self.hitstun == 0:
            if self.is_cpu and not mode_2p:
                move, jump, want_barrier, want_sword, want_gun = self.think_ai(opponent, bullets)
            elif not self.is_cpu:
                # 1P 操作 (WASD + J/K/L)
                if keys[pygame.K_LEFT]:
                    move -= 1
                if keys[pygame.K_RIGHT]:
                    move += 1
                if keys[pygame.K_UP]:
                    jump = True
                if keys[pygame.K_z]:
                    want_barrier = True
                if keys[pygame.K_x]:
                    want_sword = True
                if keys[pygame.K_c]:
                    want_gun = True
            else:
                # 2P 操作 (矢印 + N/M/,)
                if keys[pygame.K_LEFT]:
                    move -= 1
                if keys[pygame.K_RIGHT]:
                    move += 1
                if keys[pygame.K_UP]:
                    jump = True
                if keys[pygame.K_COMMA]:
                    want_barrier = True
                if keys[pygame.K_n]:
                    want_sword = True
                if keys[pygame.K_m]:
                    want_gun = True

        # 結界の制御
        if want_barrier and self.barrier_broken == 0 and self.barrier_energy > 2 and self.sword_timer == 0:
            self.barrier_active = True
            self.barrier_energy = max(0.0, self.barrier_energy - 0.85)
            if self.barrier_energy <= 0:
                self.barrier_active = False
                self.barrier_broken = 60
        else:
            self.barrier_active = False
            self.barrier_energy = min(100.0, self.barrier_energy + 0.55)

        # 攻撃実行
        if want_sword:
            self.start_sword()
        elif want_gun:
            self.start_gun(bullets, particles)

        # 移動と向き
        if self.hitstun == 0:
            speed = 0.7 if self.barrier_active else 1.85
            if self.sword_timer > 6:
                speed *= 0.4
            self.vx = self.vx * 0.65 + move * speed * 0.35
            if move != 0 and self.sword_timer == 0:
                self.facing = move
            if jump and self.on_ground and not self.barrier_active:
                self.vy = -4.6
                self.on_ground = False
        else:
            self.vx *= 0.88

        # 重力・位置更新
        self.vy += 0.25
        self.x += self.vx
        self.y += self.vy

        if self.y >= GROUND_Y - self.h:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True

        self.x = max(8, min(VIRTUAL_W - self.w - 8, self.x))

    def think_ai(self, opponent, bullets):
        move = 0
        jump = False
        want_barrier = False
        want_sword = False
        want_gun = False

        dx = opponent.x - self.x
        dist = abs(dx)
        dir_to_opp = 1 if dx > 0 else -1

        # 飛んでくる弾を検知して結界を張る
        incoming_bullet = False
        for b in bullets:
            if b.owner is not self:
                b_dx = self.center[0] - b.x
                if (b.vx > 0 and 0 < b_dx < 75) or (b.vx < 0 and -75 < b_dx < 0):
                    incoming_bullet = True
                    break

        if incoming_bullet and self.barrier_energy > 15 and self.barrier_broken == 0:
            want_barrier = True
            return move, jump, want_barrier, want_sword, want_gun

        self.ai_timer -= 1
        if self.ai_timer <= 0:
            self.ai_timer = random.randint(12, 28)
            if dist < 28:
                self.ai_action = random.choice(["sword", "sword", "retreat", "jump_away"])
            elif opponent.barrier_active and dist < 95:
                # 相手が結界中なら剣で踏み込む
                self.ai_action = "rush_sword"
            elif dist < 110:
                self.ai_action = random.choice(["approach", "gun", "gun", "barrier_bait"])
            else:
                self.ai_action = random.choice(["approach", "gun"])

        if self.ai_action == "sword":
            self.facing = dir_to_opp
            want_sword = True
        elif self.ai_action == "rush_sword":
            move = dir_to_opp
            if dist < 24:
                want_sword = True
        elif self.ai_action == "approach":
            move = dir_to_opp
        elif self.ai_action == "retreat":
            move = -dir_to_opp
        elif self.ai_action == "jump_away":
            move = -dir_to_opp
            jump = True
        elif self.ai_action == "gun":
            self.facing = dir_to_opp
            if random.random() < 0.25:
                want_gun = True
        elif self.ai_action == "barrier_bait":
            want_barrier = True

        return move, jump, want_barrier, want_sword, want_gun

    def take_damage(self, amount, knockback_dir, particles, texts, label=None, label_color=WHITE):
        self.hp = max(0, self.hp - amount)
        self.hitstun = 14
        self.flash_timer = 8
        self.vx = knockback_dir * 2.8
        self.vy = -1.6
        self.on_ground = False

        cx, cy = self.center
        for _ in range(10):
            particles.append(Particle(
                cx, cy,
                random.uniform(-2.5, 2.5),
                random.uniform(-2.5, 0.5),
                RED if amount >= 14 else YELLOW,
                random.randint(10, 20), 2
            ))
        if label:
            texts.append(FloatingText(cx, self.y - 6, label, label_color))

    def draw(self, surf):
        # 影
        pygame.draw.ellipse(surf, (10, 12, 20), (int(self.x), GROUND_Y - 2, self.w, 4))

        # 本体スプライト
        walking = abs(self.vx) > 0.4 and self.on_ground
        spr = self.sprite_walk if (walking and (self.anim_tick // 8) % 2 == 0) else self.sprite_idle
        if self.facing == -1:
            spr = pygame.transform.flip(spr, True, False)

        if self.flash_timer > 0 and self.flash_timer % 2 == 0:
            white_spr = spr.copy()
            white_spr.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(white_spr, (int(self.x), int(self.y)))
        else:
            surf.blit(spr, (int(self.x), int(self.y)))

        # 武器描画：銃
        if self.gun_timer > 0:
            gx = int(self.x + self.w - 1) if self.facing == 1 else int(self.x - 5)
            gy = int(self.y + 7)
            pygame.draw.rect(surf, (190, 200, 220), (gx, gy, 6, 3))
            pygame.draw.rect(surf, (90, 95, 110), (gx + (1 if self.facing == 1 else 3), gy + 2, 2, 2))

        # 武器描画：剣（斬撃アーク）
        if self.sword_timer > 0:
            hb = self.sword_hitbox()
            # 斬撃の閃光
            if self.sword_timer > 5:
                pygame.draw.rect(surf, WHITE, hb, 1)
                slash_y = hb.y + int((12 - self.sword_timer) * 1.6)
                pygame.draw.line(
                    surf, CYAN,
                    (hb.left, slash_y),
                    (hb.right, max(hb.top, slash_y - 6)), 2
                )
            # 剣身
            sx = int(self.x + self.w) if self.facing == 1 else int(self.x - 14)
            pygame.draw.rect(surf, WHITE, (sx, int(self.y + 6), 14, 2))
            pygame.draw.rect(surf, CYAN, (sx, int(self.y + 8), 14, 1))

        # 結界描画（銃弾を阻む半透明バリア）
        if self.barrier_active:
            cx, cy = int(self.center[0]), int(self.center[1])
            r = self.barrier_radius
            b_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pulse = int(math.sin(self.anim_tick * 0.25) * 18)
            pygame.draw.circle(b_surf, (60, 210, 255, 55 + pulse), (r + 2, r + 2), r)
            pygame.draw.circle(b_surf, (140, 245, 255, 220), (r + 2, r + 2), r, 1)
            # 六角形風のアクセントライン
            pygame.draw.circle(b_surf, (255, 255, 255, 120), (r + 2, r + 2), r - 3, 1)
            surf.blit(b_surf, (cx - r - 2, cy - r - 2))


def draw_hud(surf, p1, p2, font, mode_2p):
    # 1P HP & 結界ゲージ
    pygame.draw.rect(surf, (30, 34, 50), (10, 8, 110, 8))
    pygame.draw.rect(surf, BLUE, (10, 8, int(110 * (p1.hp / p1.max_hp)), 8))
    pygame.draw.rect(surf, WHITE, (10, 8, 110, 8), 1)

    pygame.draw.rect(surf, (20, 25, 40), (10, 18, 80, 4))
    b_col1 = RED if p1.barrier_broken > 0 else CYAN
    pygame.draw.rect(surf, b_col1, (10, 18, int(80 * (p1.barrier_energy / 100.0)), 4))

    # 2P/CPU HP & 結界ゲージ
    pygame.draw.rect(surf, (30, 34, 50), (VIRTUAL_W - 120, 8, 110, 8))
    hp2_w = int(110 * (p2.hp / p2.max_hp))
    pygame.draw.rect(surf, RED, (VIRTUAL_W - 10 - hp2_w, 8, hp2_w, 8))
    pygame.draw.rect(surf, WHITE, (VIRTUAL_W - 120, 8, 110, 8), 1)

    pygame.draw.rect(surf, (20, 25, 40), (VIRTUAL_W - 90, 18, 80, 4))
    b_col2 = RED if p2.barrier_broken > 0 else CYAN
    b2_w = int(80 * (p2.barrier_energy / 100.0))
    pygame.draw.rect(surf, b_col2, (VIRTUAL_W - 10 - b2_w, 18, b2_w, 4))

    # ラベル
    t1 = font.render("P1", False, WHITE)
    t2 = font.render("P2" if mode_2p else "CPU", False, WHITE)
    vs = font.render("VS", False, YELLOW)
    surf.blit(t1, (10, 24))
    surf.blit(t2, (VIRTUAL_W - 10 - t2.get_width(), 24))
    surf.blit(vs, (VIRTUAL_W // 2 - vs.get_width() // 2, 8))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("LOW-RES BLADE & GUN FIGHTER")
    canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    clock = pygame.time.Clock()
    font_sm = pygame.font.SysFont("consolas", 8)
    font_lg = pygame.font.SysFont("consolas", 16, bold=True)

    p1_palette = {"1": BLUE, "2": (35, 65, 130), "3": (240, 200, 170), "4": CYAN}
    p2_palette = {"1": RED, "2": (130, 35, 45), "3": (240, 200, 170), "4": YELLOW}

    p1 = Fighter(65, 1, p1_palette, is_cpu=False)
    p2 = Fighter(VIRTUAL_W - 77, -1, p2_palette, is_cpu=True)

    bullets = []
    particles = []
    texts = []

    mode_2p = False
    shake = 0
    hitstop = 0
    winner = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    p1.reset()
                    p2.reset()
                    bullets.clear()
                    particles.clear()
                    texts.clear()
                    winner = None
                elif event.key == pygame.K_TAB:
                    mode_2p = not mode_2p
                    p1.reset()
                    p2.reset()
                    bullets.clear()
                    winner = None

        keys = pygame.key.get_pressed()

        if hitstop > 0:
            hitstop -= 1
        elif winner is None:
            p1.update(p2, keys, bullets, particles, mode_2p)
            p2.update(p1, keys, bullets, particles, mode_2p)

            # --- 剣の当たり判定（結界を通過してヒット） ---
            for attacker, defender in ((p1, p2), (p2, p1)):
                if attacker.sword_timer in range(4, 11) and not attacker.sword_hit_done:
                    if attacker.sword_hitbox().colliderect(defender.rect):
                        attacker.sword_hit_done = True
                        pierced = defender.barrier_active
                        dmg = 16
                        label = "PIERCE!" if pierced else "SLASH!"
                        col = MAGENTA if pierced else WHITE
                        defender.take_damage(dmg, attacker.facing, particles, texts, label, col)
                        # 結界貫通時の特別パーティクル
                        if pierced:
                            cx, cy = defender.center
                            for _ in range(12):
                                particles.append(Particle(
                                    cx, cy,
                                    random.uniform(-3.0, 3.0),
                                    random.uniform(-2.5, 2.5),
                                    MAGENTA, 18, 2
                                ))
                        shake = 6
                        hitstop = 4

            # --- 銃弾の更新と当たり判定（結界に阻まれる） ---
            for b in bullets:
                b.update()
                if not b.alive:
                    continue
                target = p2 if b.owner is p1 else p1
                tcx, tcy = target.center
                dist = math.hypot(b.x - tcx, b.y - tcy)

                # 結界展開中なら弾をブロック
                if target.barrier_active and dist <= target.barrier_radius + b.radius:
                    b.alive = False
                    # 弾かれエフェクト
                    for _ in range(8):
                        particles.append(Particle(
                            b.x, b.y,
                            -b.vx * random.uniform(0.2, 0.5) + random.uniform(-0.8, 0.8),
                            random.uniform(-1.8, 1.8),
                            CYAN, 14, 2
                        ))
                    texts.append(FloatingText(b.x, b.y - 8, "BLOCKED", CYAN))
                    target.vx += (1 if b.vx > 0 else -1) * 0.6
                    shake = 2
                elif target.rect.collidepoint(int(b.x), int(b.y)):
                    b.alive = False
                    target.take_damage(10, 1 if b.vx > 0 else -1, particles, texts, "SHOT!", YELLOW)
                    shake = 3
                    hitstop = 2

            bullets = [b for b in bullets if b.alive]

            # 勝敗チェック
            if p1.hp <= 0:
                winner = "P2 WINS!" if mode_2p else "CPU WINS!"
            elif p2.hp <= 0:
                winner = "P1 WINS!"

        # パーティクル・テキスト更新
        for pt in particles:
            pt.update()
        particles = [pt for pt in particles if pt.life > 0]

        for tx in texts:
            tx.update()
        texts = [tx for tx in texts if tx.life > 0]

        # --- 描画 ---
        canvas.fill(BG_DARK)

        # 背景（ローレゾの都市シルエット風）
        for i in range(0, VIRTUAL_W, 24):
            h = 30 + ((i * 17) % 45)
            pygame.draw.rect(canvas, BG_MID, (i, GROUND_Y - h, 20, h))

        # 地面
        pygame.draw.rect(canvas, FLOOR_COL, (0, GROUND_Y, VIRTUAL_W, VIRTUAL_H - GROUND_Y))
        pygame.draw.line(canvas, FLOOR_LINE, (0, GROUND_Y), (VIRTUAL_W, GROUND_Y), 1)

        # キャラ・弾・エフェクト
        p1.draw(canvas)
        p2.draw(canvas)
        for b in bullets:
            b.draw(canvas)
        for pt in particles:
            pt.draw(canvas)
        for tx in texts:
            tx.draw(canvas, font_sm)

        # HUD
        draw_hud(canvas, p1, p2, font_sm, mode_2p)

        # 操作ガイド
        help_txt = "P1:WASD Move | J:Sword(Pierce) K:Gun(Blocked) L:Barrier | TAB:1P/2P R:Reset"
        h_img = font_sm.render(help_txt, False, (160, 170, 195))
        canvas.blit(h_img, (VIRTUAL_W // 2 - h_img.get_width() // 2, VIRTUAL_H - 12))

        # 勝敗表示
        if winner:
            w_img = font_lg.render(winner, False, YELLOW)
            sub_img = font_sm.render("Press R to Rematch", False, WHITE)
            canvas.blit(w_img, (VIRTUAL_W // 2 - w_img.get_width() // 2, 62))
            canvas.blit(sub_img, (VIRTUAL_W // 2 - sub_img.get_width() // 2, 84))

        # 画面揺れを適用して拡大描画
        ox = random.randint(-shake, shake) if shake > 0 else 0
        oy = random.randint(-shake, shake) if shake > 0 else 0
        if shake > 0:
            shake -= 1

        scaled = pygame.transform.scale(canvas, (SCREEN_W, SCREEN_H))
        screen.fill((0, 0, 0))
        screen.blit(scaled, (ox * SCALE, oy * SCALE))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
