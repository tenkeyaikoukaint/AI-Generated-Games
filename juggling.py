import pygame
import sys
import math
import random

# --- 初期設定 ---
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Side View Tennis - 2-Ball Juggle Edition")

# 色の定義
WHITE = (255, 255, 255)
GRAY = (120, 120, 130)
DARK_BG = (18, 22, 32)
BLUE = (50, 160, 255)
CYAN = (100, 230, 255)
RED = (255, 95, 95)
YELLOW = (255, 215, 70)
GREEN = (80, 230, 140)

# --- ゲームパラメータ ---
FPS = 60
BASE_GRAVITY = 0.28      # 2ボールで扱いやすいようにわずかに調整
BOUNCE_STRENGTH = -14.5  # パドルで打ったときの上昇力
MAX_VX = 9.5             # 横速度の上限（暴走防止）


# --- エフェクト用クラス ---

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 5.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(15, 30)
        self.max_life = self.life
        self.color = color
        self.radius = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            ratio = self.life / self.max_life
            r = max(1, int(self.radius * ratio))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 45

    def update(self):
        self.y -= 1.2
        self.life -= 1

    def draw(self, surface, font):
        if self.life > 0:
            img = font.render(self.text, True, self.color)
            surface.blit(img, (int(self.x - img.get_width() / 2), int(self.y)))


# --- ゲームオブジェクト ---

class Ball:
    def __init__(self, ball_id, color, start_x, initial_vx, delay_frames=0):
        self.ball_id = ball_id
        self.color = color
        self.radius = 15
        self.default_x = start_x
        self.default_vx = initial_vx
        self.trail = []
        self.reset(delay_frames)

    def reset(self, delay_frames=60):
        self.x = self.default_x
        self.y = HEIGHT // 4
        # 毎回少しだけランダム性を入れて単調さを防ぐ
        self.vx = self.default_vx + random.uniform(-1.0, 1.0)
        self.vy = 0
        self.respawn_timer = delay_frames
        self.trail.clear()

    def move(self, gravity):
        # リスポーン待機中は動かない
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            return

        # 軌跡を記録
        self.trail.append((self.x, self.y))
        if len(self.trail) > 12:
            self.trail.pop(0)

        # 重力と位置更新
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

        # 横速度の上限クランプ
        self.vx = max(-MAX_VX, min(MAX_VX, self.vx))

        # 左右の壁（Yベクトル維持でXのみ反転）
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -1
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -1

        # 天井
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -0.8

    def draw(self, surface):
        # リスポーン待機中は点滅表示
        if self.respawn_timer > 0:
            if (self.respawn_timer // 6) % 2 == 0:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius, 2)
            return

        # 軌跡の描画
        for i, (tx, ty) in enumerate(self.trail):
            ratio = (i + 1) / len(self.trail)
            r = max(2, int(self.radius * ratio * 0.65))
            faded_color = (
                int(self.color[0] * ratio * 0.5),
                int(self.color[1] * ratio * 0.5),
                int(self.color[2] * ratio * 0.5),
            )
            pygame.draw.circle(surface, faded_color, (int(tx), int(ty)), r)

        # 本体とハイライト
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x - 4), int(self.y - 4)), 4)


class Paddle:
    def __init__(self):
        self.width = 125
        self.height = 18
        self.base_y = HEIGHT - 50
        self.speed = 9.5
        self.dash_speed = 16.0
        self.hit_offset = 0.0  # ヒット時の沈み込み演出用
        self.is_dashing = False
        self.rect = pygame.Rect(WIDTH // 2 - self.width // 2, self.base_y, self.width, self.height)

    def move(self):
        keys = pygame.key.get_pressed()
        self.is_dashing = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        current_speed = self.dash_speed if self.is_dashing else self.speed

        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= current_speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += current_speed

        # 画面外にはみ出さないように補正
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)

        # 沈み込みから元の位置に戻る
        if self.hit_offset > 0:
            self.hit_offset = max(0.0, self.hit_offset - 0.8)
        self.rect.y = int(self.base_y + self.hit_offset)

    def trigger_hit(self):
        self.hit_offset = 6.0

    def draw(self, surface):
        color = CYAN if self.is_dashing else BLUE
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        # 上面のハイライト線
        pygame.draw.line(surface, WHITE, (self.rect.left + 6, self.rect.top + 3),
                         (self.rect.right - 6, self.rect.top + 3), 2)


# --- ボール同士の衝突判定 ---

def handle_ball_collision(b1, b2, particles):
    if b1.respawn_timer > 0 or b2.respawn_timer > 0:
        return

    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)
    min_dist = b1.radius + b2.radius

    if 0 < dist < min_dist:
        # 単位法線ベクトル
        nx = dx / dist
        ny = dy / dist

        # 重なりを解消
        overlap = (min_dist - dist) / 2.0
        b1.x -= nx * overlap
        b1.y -= ny * overlap
        b2.x += nx * overlap
        b2.y += ny * overlap

        # 法線方向の相対速度を計算して弾性衝突
        dvx = b1.vx - b2.vx
        dvy = b1.vy - b2.vy
        dot = dvx * nx + dvy * ny

        if dot > 0:
            b1.vx -= dot * nx
            b1.vy -= dot * ny
            b2.vx += dot * nx
            b2.vy += dot * ny

            # 衝突点にスパーク発生
            cx = (b1.x + b2.x) / 2
            cy = (b1.y + b2.y) / 2
            for _ in range(8):
                particles.append(Particle(cx, cy, WHITE))


# --- メインループ ---

def main():
    clock = pygame.time.Clock()
    font_ui = pygame.font.SysFont(None, 28)
    font_small = pygame.font.SysFont(None, 22)
    font_big = pygame.font.SysFont(None, 64)

    high_score = 0

    def create_game_state():
        # 2つのボール：左右の位置と初速をずらし、2個目は少し遅れてスタート
        balls = [
            Ball(ball_id=0, color=RED, start_x=WIDTH // 3, initial_vx=4.2, delay_frames=20),
            Ball(ball_id=1, color=YELLOW, start_x=WIDTH * 2 // 3, initial_vx=-4.2, delay_frames=85),
        ]
        return {
            "balls": balls,
            "paddle": Paddle(),
            "particles": [],
            "texts": [],
            "score": 0,
            "lives": 3,
            "combo": 0,
            "last_hit_id": -1,
            "game_over": False,
        }

    state = create_game_state()

    running = True
    while running:
        # 1. イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    state = create_game_state()

        # 2. 更新処理
        if not state["game_over"]:
            paddle = state["paddle"]
            balls = state["balls"]

            # スコアに応じて重力をわずかに上げ、緊張感を高める（上限あり）
            current_gravity = min(0.42, BASE_GRAVITY + state["score"] * 0.00012)

            paddle.move()

            for ball in balls:
                ball.move(current_gravity)

                # パドルとの衝突判定（落下中のみ）
                if ball.respawn_timer == 0 and ball.vy > 0:
                    ball_rect = pygame.Rect(
                        ball.x - ball.radius, ball.y - ball.radius,
                        ball.radius * 2, ball.radius * 2
                    )
                    if ball_rect.colliderect(paddle.rect):
                        if ball.y + ball.radius < paddle.rect.centery + 14:
                            ball.y = paddle.rect.top - ball.radius
                            ball.vy = BOUNCE_STRENGTH

                            # パドルの当たった位置で横速度を変化
                            hit_pos = (ball.x - paddle.rect.centerx) / (paddle.width / 2)
                            ball.vx += hit_pos * 3.8
                            paddle.trigger_hit()

                            # コンボ＆スコア計算（交互打ちでジャグリングボーナス）
                            state["combo"] += 1
                            is_juggle = (state["last_hit_id"] != -1 and state["last_hit_id"] != ball.ball_id)
                            state["last_hit_id"] = ball.ball_id

                            base_points = 10
                            multiplier = min(5, 1 + state["combo"] // 4)
                            if is_juggle:
                                points = base_points * multiplier * 2
                                msg = f"+{points} JUGGLE!"
                                text_color = GREEN
                            else:
                                points = base_points * multiplier
                                msg = f"+{points}"
                                text_color = WHITE

                            state["score"] += points
                            high_score = max(high_score, state["score"])

                            state["texts"].append(FloatingText(ball.x, paddle.rect.top - 15, msg, text_color))
                            for _ in range(10):
                                state["particles"].append(Particle(ball.x, paddle.rect.top, ball.color))

                # 落下ミス判定
                if ball.y > HEIGHT + 40:
                    state["lives"] -= 1
                    state["combo"] = 0
                    state["last_hit_id"] = -1
                    state["texts"].append(FloatingText(ball.x, HEIGHT - 40, "MISS!", RED))

                    if state["lives"] <= 0:
                        state["game_over"] = True
                    else:
                        ball.reset(delay_frames=70)

            # 2つのボール同士の衝突
            handle_ball_collision(balls[0], balls[1], state["particles"])

        # エフェクト更新
        for p in state["particles"][:]:
            p.update()
            if p.life <= 0:
                state["particles"].remove(p)

        for t in state["texts"][:]:
            t.update()
            if t.life <= 0:
                state["texts"].remove(t)

        # 3. 描画処理
        screen.fill(DARK_BG)

        # ガイド線（地面）
        pygame.draw.line(screen, GRAY, (0, HEIGHT - 10), (WIDTH, HEIGHT - 10), 2)

        state["paddle"].draw(screen)
        for ball in state["balls"]:
            ball.draw(screen)
        for p in state["particles"]:
            p.draw(screen)
        for t in state["texts"]:
            t.draw(screen, font_small)

        # UI表示
        score_surf = font_ui.render(f"SCORE: {state['score']}   HIGH: {high_score}", True, WHITE)
        screen.blit(score_surf, (15, 12))

        combo_color = GREEN if state["combo"] >= 4 else WHITE
        combo_surf = font_ui.render(f"COMBO: {state['combo']}", True, combo_color)
        screen.blit(combo_surf, (15, 42))

        # ライフ表示（右上に丸アイコン）
        lives_label = font_ui.render("LIVES:", True, WHITE)
        screen.blit(lives_label, (WIDTH - 170, 12))
        for i in range(3):
            color = RED if i < state["lives"] else (50, 50, 60)
            pygame.draw.circle(screen, color, (WIDTH - 85 + i * 28, 22), 9)

        # 操作説明
        help_text = font_small.render("Left/Right: Move | Shift: Dash | Space: Reset", True, GRAY)
        screen.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, HEIGHT - 32))

        # ゲームオーバーオーバーレイ
        if state["game_over"]:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            go_surf = font_big.render("GAME OVER", True, RED)
            retry_surf = font_ui.render("Press SPACE to Retry", True, WHITE)
            screen.blit(go_surf, (WIDTH // 2 - go_surf.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(retry_surf, (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()