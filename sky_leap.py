import random
import pygame

# 画面・3D設定
WIDTH, HEIGHT = 800, 600
FOV = 500
FPS = 60


class Building:
    def __init__(self, x, z, w, d, top_y):
        self.x1, self.x2 = x - w / 2, x + w / 2
        self.z1, self.z2 = z, z + d
        self.top_y = top_y
        self.bottom_y = -40.0
        # 距離や個体ごとの色バリエーション
        shade = random.randint(45, 75)
        self.top_color = (shade + 35, shade + 45, shade + 65)
        self.side_color = (shade, shade + 10, shade + 25)
        self.front_color = (shade - 15, shade - 5, shade + 10)


def project(x, y, z, cam_x, cam_y, cam_z):
    """3D座標を2D画面座標へ透視投影"""
    rz = z - cam_z
    if rz <= 0.5:
        return None
    scale = FOV / rz
    sx = WIDTH * 0.5 + (x - cam_x) * scale
    sy = HEIGHT * 0.42 - (y - cam_y) * scale
    return (sx, sy)


def draw_quad(surface, color, pts3d, cam):
    pts2d = [project(x, y, z, *cam) for x, y, z in pts3d]
    if any(p is None for p in pts2d):
        return
    pygame.draw.polygon(surface, color, pts2d)
    pygame.draw.polygon(surface, (20, 25, 35), pts2d, 1)


def generate_next_building(prev):
    gap = random.uniform(3.0, 5.5)
    w = random.uniform(4.5, 8.0)
    d = random.uniform(10.0, 18.0)
    # 前のビルから左右・高さを少しずらす
    prev_cx = (prev.x1 + prev.x2) * 0.5
    cx = prev_cx + random.uniform(-4.0, 4.0)
    top_y = max(-4.0, min(6.0, prev.top_y + random.uniform(-1.8, 1.5)))
    return Building(cx, prev.z2 + gap, w, d, top_y)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Sky Leap 3D (Pygame Simple)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    def reset():
        b0 = Building(0.0, 0.0, 8.0, 20.0, 0.0)
        buildings = [b0]
        for _ in range(12):
            buildings.append(generate_next_building(buildings[-1]))
        player = {
            "x": 0.0, "y": 0.0, "z": 3.0,
            "vy": 0.0, "speed": 14.0,
            "on_ground": True, "coyote": 0.0,
        }
        return buildings, player, False

    buildings, p, game_over = reset()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # 入力処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_over:
                    buildings, p, game_over = reset()
                elif event.key == pygame.K_SPACE and not game_over:
                    if p["on_ground"] or p["coyote"] > 0:
                        p["vy"] = 13.5
                        p["on_ground"] = False
                        p["coyote"] = 0.0

        # 更新処理
        if not game_over:
            keys = pygame.key.get_pressed()
            move_x = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                move_x -= 1.0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                move_x += 1.0

            prev_y = p["y"]
            p["x"] += move_x * 11.0 * dt
            p["z"] += p["speed"] * dt
            p["speed"] = min(24.0, p["speed"] + 0.15 * dt)

            p["vy"] -= 32.0 * dt
            p["y"] += p["vy"] * dt

            # 屋上との着地判定
            landed = False
            ground_y = None
            for b in buildings:
                if b.x1 - 0.4 <= p["x"] <= b.x2 + 0.4 and b.z1 - 0.4 <= p["z"] <= b.z2 + 0.4:
                    ground_y = b.top_y
                    if p["vy"] <= 0 and prev_y >= b.top_y - 0.5 and p["y"] <= b.top_y:
                        p["y"] = b.top_y
                        p["vy"] = 0.0
                        landed = True
                        break

            p["on_ground"] = landed
            p["coyote"] = 0.12 if landed else max(0.0, p["coyote"] - dt)

            if p["y"] < -15.0:
                game_over = True

            # ビルの入れ替え（後ろを消して前を追加）
            if buildings[0].z2 < p["z"] - 12.0:
                buildings.pop(0)
                buildings.append(generate_next_building(buildings[-1]))
        else:
            ground_y = None

        # カメラ位置（3人称・後方やや上空）
        cam = (p["x"] * 0.7, p["y"] + 4.2, p["z"] - 8.5)

        # 描画（空）
        screen.fill((18, 24, 42))

        # ビルを奥から手前へ描画（画家のアルゴリズム）
        for b in sorted(buildings, key=lambda b: b.z2, reverse=True):
            z1 = max(b.z1, cam[2] + 0.6)
            z2 = b.z2
            if z2 <= z1:
                continue

            # 側面（カメラから見える側のみ）
            if cam[0] < b.x1:
                draw_quad(screen, b.side_color, [
                    (b.x1, b.top_y, z1), (b.x1, b.top_y, z2),
                    (b.x1, b.bottom_y, z2), (b.x1, b.bottom_y, z1)
                ], cam)
            elif cam[0] > b.x2:
                draw_quad(screen, b.side_color, [
                    (b.x2, b.top_y, z1), (b.x2, b.top_y, z2),
                    (b.x2, b.bottom_y, z2), (b.x2, b.bottom_y, z1)
                ], cam)

            # 前面
            if b.z1 > cam[2] + 0.6:
                draw_quad(screen, b.front_color, [
                    (b.x1, b.top_y, z1), (b.x2, b.top_y, z1),
                    (b.x2, b.bottom_y, z1), (b.x1, b.bottom_y, z1)
                ], cam)

            # 屋上面
            draw_quad(screen, b.top_color, [
                (b.x1, b.top_y, z1), (b.x2, b.top_y, z1),
                (b.x2, b.top_y, z2), (b.x1, b.top_y, z2)
            ], cam)

        # 足元の影（屋上の真上にいるときだけ表示）
        if ground_y is not None and p["y"] >= ground_y:
            sp = project(p["x"], ground_y, p["z"], *cam)
            if sp:
                r = max(4, int(18 - (p["y"] - ground_y) * 1.5))
                pygame.draw.ellipse(screen, (10, 12, 20), (sp[0] - r, sp[1] - r * 0.4, r * 2, r * 0.8))

        # プレイヤー（簡易ボックス）
        px, py, pz = p["x"], p["y"], p["z"]
        pw, ph = 0.45, 1.3
        draw_quad(screen, (255, 110, 80), [
            (px - pw, py + ph, pz), (px + pw, py + ph, pz),
            (px + pw, py, pz), (px - pw, py, pz)
        ], cam)

        # UI
        score_text = font.render(f"DIST: {int(p['z'])} m", True, (240, 245, 255))
        screen.blit(score_text, (20, 20))

        if game_over:
            over_text = font.render("GAME OVER  -  Press R to Retry", True, (255, 100, 100))
            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()