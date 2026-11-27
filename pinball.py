import math
import sys
import pygame

# --- 定数設定 ---
WIDTH, HEIGHT = 450, 700
FPS = 60
SUBSTEPS = 8  # 1フレームあたりの物理計算回数（すり抜け防止）

GRAVITY = 0.25
BALL_RADIUS = 10
MAX_SPEED = 24.0

# 色定義
BG_COLOR = (18, 22, 34)
WALL_COLOR = (100, 140, 200)
BALL_COLOR = (240, 245, 255)
FLIPPER_COLOR = (255, 190, 60)
BUMPER_COLOR = (230, 70, 100)
BUMPER_FLASH = (255, 240, 180)
PLUNGER_COLOR = (80, 210, 160)
TEXT_COLOR = (230, 235, 245)


class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 410.0
        self.y = 650.0
        self.vx = 0.0
        self.vy = 0.0
        self.radius = BALL_RADIUS

    def in_shooter_lane(self):
        return self.x > 385 and self.y > 580

    def update(self, dt_scale):
        self.vy += GRAVITY * dt_scale
        # 空気抵抗（ごくわずかに減衰）
        self.vx *= 1.0 - 0.001 * dt_scale
        self.vy *= 1.0 - 0.001 * dt_scale

        # 速度上限
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale

        self.x += self.vx * dt_scale
        self.y += self.vy * dt_scale

    def draw(self, surface):
        pygame.draw.circle(surface, BALL_COLOR, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (180, 195, 220), (int(self.x) - 3, int(self.y) - 3), 3)


class Bumper:
    def __init__(self, x, y, radius, score_value=100, bounce=1.25):
        self.x = x
        self.y = y
        self.radius = radius
        self.score_value = score_value
        self.bounce = bounce
        self.flash_timer = 0

    def collide(self, ball):
        dx = ball.x - self.x
        dy = ball.y - self.y
        dist = math.hypot(dx, dy)
        min_dist = self.radius + ball.radius

        if dist < min_dist and dist > 0:
            nx = dx / dist
            ny = dy / dist
            # めり込み解消
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.y += ny * overlap

            # 反射＋弾き飛ばし
            dot = ball.vx * nx + ball.vy * ny
            if dot < 0:
                ball.vx -= 2 * dot * nx
                ball.vy -= 2 * dot * ny
            # 最低限の反発速度を保証
            speed = max(math.hypot(ball.vx, ball.vy) * self.bounce, 9.0)
            ball.vx = nx * speed
            ball.vy = ny * speed

            self.flash_timer = 8
            return self.score_value
        return 0

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface):
        color = BUMPER_FLASH if self.flash_timer > 0 else BUMPER_COLOR
        r = self.radius + (3 if self.flash_timer > 0 else 0)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), r - 6, 2)


class Flipper:
    def __init__(self, x, y, length, rest_deg, active_deg):
        self.x = x
        self.y = y
        self.length = length
        self.thickness = 8
        self.rest_angle = math.radians(rest_deg)
        self.active_angle = math.radians(active_deg)
        self.angle = self.rest_angle
        self.omega = 0.0  # rad / frame
        self.speed = 0.32  # 回転速度

    def update(self, pressed, dt_scale):
        target = self.active_angle if pressed else self.rest_angle
        diff = target - self.angle
        step = self.speed * dt_scale

        if abs(diff) <= step:
            self.omega = diff / dt_scale if dt_scale > 0 else 0.0
            self.angle = target
        else:
            direction = 1 if diff > 0 else -1
            self.angle += direction * step
            self.omega = direction * self.speed

    def get_tip(self):
        return (
            self.x + math.cos(self.angle) * self.length,
            self.y + math.sin(self.angle) * self.length,
        )

    def collide(self, ball):
        x1, y1 = self.x, self.y
        x2, y2 = self.get_tip()
        return collide_ball_segment(
            ball, x1, y1, x2, y2, thickness=self.thickness,
            restitution=0.75, pivot=(self.x, self.y), omega=self.omega
        )

    def draw(self, surface):
        tip = self.get_tip()
        pygame.draw.line(surface, FLIPPER_COLOR, (self.x, self.y), tip, self.thickness * 2)
        pygame.draw.circle(surface, FLIPPER_COLOR, (int(self.x), int(self.y)), self.thickness)
        pygame.draw.circle(surface, FLIPPER_COLOR, (int(tip[0]), int(tip[1])), self.thickness)
        pygame.draw.circle(surface, BG_COLOR, (int(self.x), int(self.y)), 4)


def collide_ball_segment(ball, x1, y1, x2, y2, thickness=2, restitution=0.75, pivot=None, omega=0.0):
    """ボールと線分（壁またはフリッパー）の衝突判定と反射"""
    sx = x2 - x1
    sy = y2 - y1
    seg_len_sq = sx * sx + sy * sy
    if seg_len_sq == 0:
        return False

    t = ((ball.x - x1) * sx + (ball.y - y1) * sy) / seg_len_sq
    t = max(0.0, min(1.0, t))

    cx = x1 + t * sx
    cy = y1 + t * sy

    dx = ball.x - cx
    dy = ball.y - cy
    dist = math.hypot(dx, dy)
    min_dist = ball.radius + thickness

    if dist < min_dist and dist > 0:
        nx = dx / dist
        ny = dy / dist

        # めり込み解消
        overlap = min_dist - dist
        ball.x += nx * overlap
        ball.y += ny * overlap

        # 接点における線分の速度（フリッパー回転用）
        seg_vx, seg_vy = 0.0, 0.0
        if pivot is not None and omega != 0.0:
            rx = cx - pivot[0]
            ry = cy - pivot[1]
            seg_vx = -omega * ry
            seg_vy = omega * rx

        # 相対速度で反射計算
        rvx = ball.vx - seg_vx
        rvy = ball.vy - seg_vy
        vel_along_normal = rvx * nx + rvy * ny

        if vel_along_normal < 0:
            impulse = -(1.0 + restitution) * vel_along_normal
            ball.vx += impulse * nx
            ball.vy += impulse * ny
            return True
    return False


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Pinball")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22, bold=True)
    big_font = pygame.font.SysFont("arial", 40, bold=True)

    # 壁の定義: (x1, y1, x2, y2)
    walls = [
        # 外枠
        (15, 70, 15, 685),       # 左壁
        (70, 15, 365, 15),       # 上壁
        (15, 70, 70, 15),        # 左上斜め
        (365, 15, 435, 85),      # 右上カーブ用斜め
        (435, 85, 435, 685),     # 右壁
        (385, 685, 435, 685),    # 発射レーン底
        # 発射レーン仕切り壁
        (385, 145, 385, 685),
        # フリッパーへ誘導する斜め壁
        (15, 535, 115, 610),     # 左ガイド
        (385, 535, 285, 610),    # 右ガイド
        # 上部のアクセント壁（スリングショット風）
        (65, 440, 105, 515),
        (335, 440, 295, 515),
    ]

    bumpers = [
        Bumper(200, 170, 26, score_value=100),
        Bumper(115, 250, 22, score_value=100),
        Bumper(285, 250, 22, score_value=100),
        Bumper(200, 330, 20, score_value=150),
    ]

    left_flipper = Flipper(115, 610, length=70, rest_deg=28, active_deg=-30)
    right_flipper = Flipper(285, 610, length=70, rest_deg=152, active_deg=210)

    ball = Ball()
    score = 0
    lives = 3
    game_over = False

    plunger_charge = 0.0
    charging = False

    while True:
        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    score = 0
                    lives = 3
                    game_over = False
                    ball.reset()
                elif event.key == pygame.K_SPACE and not game_over and ball.in_shooter_lane():
                    charging = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and charging:
                    if ball.in_shooter_lane():
                        ball.vy = -(16.0 + plunger_charge * 10.0)
                        ball.vx = -0.3  # わずかに左へ寄せる
                    charging = False
                    plunger_charge = 0.0

        keys = pygame.key.get_pressed()
        left_pressed = keys[pygame.K_LEFT] or keys[pygame.K_z]
        right_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_SLASH]

        if charging:
            plunger_charge = min(1.0, plunger_charge + 0.025)

        # --- 物理更新（サブステップ） ---
        if not game_over:
            dt_scale = 1.0 / SUBSTEPS
            for _ in range(SUBSTEPS):
                left_flipper.update(left_pressed, dt_scale)
                right_flipper.update(right_pressed, dt_scale)
                ball.update(dt_scale)

                # 壁との衝突
                for w in walls:
                    collide_ball_segment(ball, w[0], w[1], w[2], w[3], thickness=3, restitution=0.7)

                # バンパーとの衝突
                for bumper in bumpers:
                    score += bumper.collide(ball)

                # フリッパーとの衝突
                left_flipper.collide(ball)
                right_flipper.collide(ball)

            for bumper in bumpers:
                bumper.update()

            # 落下判定
            if ball.y > HEIGHT + 20:
                lives -= 1
                if lives <= 0:
                    game_over = True
                else:
                    ball.reset()

        # --- 描画 ---
        screen.fill(BG_COLOR)

        # 壁
        for w in walls:
            pygame.draw.line(screen, WALL_COLOR, (w[0], w[1]), (w[2], w[3]), 6)

        # プランジャー（発射台）の描画
        plunger_top = 662 + int(plunger_charge * 18)
        pygame.draw.rect(screen, PLUNGER_COLOR, (395, plunger_top, 30, 682 - plunger_top))

        # バンパー・フリッパー・ボール
        for bumper in bumpers:
            bumper.draw(screen)
        left_flipper.draw(screen)
        right_flipper.draw(screen)
        if not game_over:
            ball.draw(screen)

        # UI（スコア・残機）
        score_surf = font.render(f"SCORE: {score}", True, TEXT_COLOR)
        lives_surf = font.render(f"BALLS: {lives}", True, TEXT_COLOR)
        screen.blit(score_surf, (25, 25))
        screen.blit(lives_surf, (270, 25))

        if ball.in_shooter_lane() and not game_over:
            hint = font.render("Hold SPACE to launch", True, PLUNGER_COLOR)
            screen.blit(hint, (105, 390))

        if game_over:
            over_surf = big_font.render("GAME OVER", True, (255, 90, 90))
            retry_surf = font.render("Press R to Restart", True, TEXT_COLOR)
            screen.blit(over_surf, (WIDTH // 2 - over_surf.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(retry_surf, (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 15))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()