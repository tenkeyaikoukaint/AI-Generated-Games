import colorsys
import sys
import pygame


def generate_sierpinski_points(level: int) -> list[tuple[float, float]]:
    """指定した次数(level)のシェルピンスキー曲線の頂点リストを生成する"""
    points = [(0.0, 0.0)]
    x, y = 0.0, 0.0
    h = 1.0

    def move(dx: float, dy: float):
        nonlocal x, y
        x += dx
        y += dy
        points.append((x, y))

    def sierp_a(n: int):
        if n > 0:
            sierp_a(n - 1)
            move(h, h)
            sierp_b(n - 1)
            move(2 * h, 0)
            sierp_d(n - 1)
            move(h, -h)
            sierp_a(n - 1)

    def sierp_b(n: int):
        if n > 0:
            sierp_b(n - 1)
            move(-h, h)
            sierp_c(n - 1)
            move(0, 2 * h)
            sierp_a(n - 1)
            move(h, h)
            sierp_b(n - 1)

    def sierp_c(n: int):
        if n > 0:
            sierp_c(n - 1)
            move(-h, -h)
            sierp_d(n - 1)
            move(-2 * h, 0)
            sierp_b(n - 1)
            move(-h, h)
            sierp_c(n - 1)

    def sierp_d(n: int):
        if n > 0:
            sierp_d(n - 1)
            move(h, -h)
            sierp_a(n - 1)
            move(0, -2 * h)
            sierp_c(n - 1)
            move(-h, -h)
            sierp_d(n - 1)

    # 閉じた曲線を構成
    sierp_a(level)
    move(h, h)
    sierp_b(level)
    move(-h, h)
    sierp_c(level)
    move(-h, -h)
    sierp_d(level)
    move(h, -h)

    return points


def fit_points_to_screen(
    points: list[tuple[float, float]], width: int, height: int, margin: int = 70
) -> list[tuple[int, int]]:
    """頂点群を画面中央に収まるようスケーリング・平行移動する"""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max_x - min_x
    span_y = max_y - min_y
    scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_y)

    offset_x = (width - span_x * scale) / 2 - min_x * scale
    offset_y = (height - span_y * scale) / 2 - min_y * scale

    return [(int(x * scale + offset_x), int(y * scale + offset_y)) for x, y in points]


def hsv_color(progress: float) -> tuple[int, int, int]:
    """進捗(0.0〜1.0)に応じたRGBカラーを返す"""
    r, g, b = colorsys.hsv_to_rgb(progress * 0.85, 0.85, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def main():
    pygame.init()
    WIDTH, HEIGHT = 800, 800
    BG_COLOR = (18, 20, 28)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Sierpinski Curve Animation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    # 描画用サーフェス（線分を累積描画して高次数でも軽く保つ）
    canvas = pygame.Surface((WIDTH, HEIGHT))

    level = 4
    speed = 4  # 1フレームあたりに描画する線分数
    paused = False

    def reset_curve(new_level: int):
        raw_pts = generate_sierpinski_points(new_level)
        pts = fit_points_to_screen(raw_pts, WIDTH, HEIGHT)
        canvas.fill(BG_COLOR)
        return pts, 0

    points, current_idx = reset_curve(level)
    total_segments = len(points) - 1

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    points, current_idx = reset_curve(level)
                    total_segments = len(points) - 1
                elif event.key == pygame.K_UP and level < 6:
                    level += 1
                    points, current_idx = reset_curve(level)
                    total_segments = len(points) - 1
                elif event.key == pygame.K_DOWN and level > 1:
                    level -= 1
                    points, current_idx = reset_curve(level)
                    total_segments = len(points) - 1
                elif event.key == pygame.K_RIGHT:
                    speed = min(speed * 2, 256)
                elif event.key == pygame.K_LEFT:
                    speed = max(speed // 2, 1)

        # 徐々に線分を描画
        if not paused and current_idx < total_segments:
            steps = min(speed, total_segments - current_idx)
            line_width = 3 if level <= 3 else (2 if level == 4 else 1)
            for _ in range(steps):
                p1 = points[current_idx]
                p2 = points[current_idx + 1]
                color = hsv_color(current_idx / total_segments)
                pygame.draw.line(canvas, color, p1, p2, line_width)
                current_idx += 1

        # 画面出力
        screen.blit(canvas, (0, 0))

        # 先端のマーカー（描画中のみ表示）
        if current_idx < total_segments:
            pygame.draw.circle(screen, (255, 255, 255), points[current_idx], 4)

        # ステータス表示
        status = (
            f"Level: {level} (Up/Down) | "
            f"Speed: {speed}x (Left/Right) | "
            f"Progress: {current_idx}/{total_segments} | "
            f"[Space] Pause  [R] Reset"
        )
        text_surface = font.render(status, True, (220, 225, 235))
        screen.blit(text_surface, (16, 16))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()