import pygame
import sys

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
BG_COLOR = (18, 18, 24)
PADDLE_COLOR = (220, 220, 230)
BALL_COLOR = (255, 255, 255)
TEXT_COLOR = (200, 200, 210)
ROW_COLORS = [
    (220, 70, 70),    # Red
    (230, 140, 50),   # Orange
    (230, 210, 60),   # Yellow
    (70, 200, 110),   # Green
    (70, 150, 230),   # Blue
]

# Dimensions
PADDLE_W, PADDLE_H = 110, 14
BALL_RADIUS = 8
ROWS, COLS = 5, 10
BRICK_GAP = 6
BRICK_W = (WIDTH - (COLS + 1) * BRICK_GAP) // COLS
BRICK_H = 24
TOP_OFFSET = 60


def create_bricks():
    bricks = []
    for row in range(ROWS):
        color = ROW_COLORS[row % len(ROW_COLORS)]
        for col in range(COLS):
            x = BRICK_GAP + col * (BRICK_W + BRICK_GAP)
            y = TOP_OFFSET + row * (BRICK_H + BRICK_GAP)
            bricks.append((pygame.Rect(x, y, BRICK_W, BRICK_H), color))
    return bricks


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Breakout")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 24, bold=True)

    def reset_game():
        paddle = pygame.Rect((WIDTH - PADDLE_W) // 2, HEIGHT - 40, PADDLE_W, PADDLE_H)
        ball_pos = [float(WIDTH // 2), float(HEIGHT - 60)]
        ball_vel = [4.5, -4.5]
        bricks = create_bricks()
        return paddle, ball_pos, ball_vel, bricks, 0, "PLAYING"

    paddle, ball_pos, ball_vel, bricks, score, state = reset_game()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE and state != "PLAYING":
                    paddle, ball_pos, ball_vel, bricks, score, state = reset_game()

        keys = pygame.key.get_pressed()
        if state == "PLAYING":
            # Paddle movement (Left/Right arrows or A/D)
            speed = 8
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and paddle.left > 0:
                paddle.x -= speed
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and paddle.right < WIDTH:
                paddle.x += speed

            # Move ball
            ball_pos[0] += ball_vel[0]
            ball_pos[1] += ball_vel[1]

            ball_rect = pygame.Rect(
                int(ball_pos[0] - BALL_RADIUS),
                int(ball_pos[1] - BALL_RADIUS),
                BALL_RADIUS * 2,
                BALL_RADIUS * 2,
            )

            # Wall collisions
            if ball_rect.left <= 0:
                ball_pos[0] = BALL_RADIUS
                ball_vel[0] *= -1
            elif ball_rect.right >= WIDTH:
                ball_pos[0] = WIDTH - BALL_RADIUS
                ball_vel[0] *= -1

            if ball_rect.top <= 0:
                ball_pos[1] = BALL_RADIUS
                ball_vel[1] *= -1
            elif ball_rect.bottom >= HEIGHT:
                state = "GAME OVER"

            # Paddle collision with angle control
            if ball_rect.colliderect(paddle) and ball_vel[1] > 0:
                ball_pos[1] = paddle.top - BALL_RADIUS
                offset = (ball_pos[0] - paddle.centerx) / (PADDLE_W / 2)
                ball_vel[0] = offset * 6.0
                ball_vel[1] = -abs(ball_vel[1])

            # Brick collisions
            for i, (brick, color) in enumerate(bricks):
                if ball_rect.colliderect(brick):
                    # Determine bounce axis based on overlap
                    overlap_left = ball_rect.right - brick.left
                    overlap_right = brick.right - ball_rect.left
                    overlap_top = ball_rect.bottom - brick.top
                    overlap_bottom = brick.bottom - ball_rect.top

                    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                    if min_overlap in (overlap_left, overlap_right):
                        ball_vel[0] *= -1
                    else:
                        ball_vel[1] *= -1

                    bricks.pop(i)
                    score += 10
                    break

            if not bricks:
                state = "YOU WIN!"

        # --- Render ---
        screen.fill(BG_COLOR)

        for brick, color in bricks:
            pygame.draw.rect(screen, color, brick, border_radius=3)

        pygame.draw.rect(screen, PADDLE_COLOR, paddle, border_radius=4)
        pygame.draw.circle(screen, BALL_COLOR, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

        score_surf = font.render(f"SCORE: {score}", True, TEXT_COLOR)
        screen.blit(score_surf, (16, 16))

        if state != "PLAYING":
            msg = font.render(f"{state} - PRESS SPACE TO RESTART", True, (255, 255, 255))
            rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            screen.blit(msg, rect)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()