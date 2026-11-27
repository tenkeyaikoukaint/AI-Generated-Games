
import pygame
import math
import colorsys

# --- 設定 ---
WIDTH, HEIGHT = 800, 600
FPS = 60
BG_COLOR = (0, 0, 0)
FADE_ALPHA = 15  # 残像の残り具合（小さいほど長く残る 0-255）
PARTICLE_COUNT = 300  # 粒子の数
SPEED_FACTOR = 0.005  # 全体の動きの速さ

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Math Therapy - Sine Waves")
    clock = pygame.time.Clock()

    # 残像用サーフェス（半透明の黒い膜）
    fade_surface = pygame.Surface((WIDTH, HEIGHT))
    fade_surface.fill(BG_COLOR)
    fade_surface.set_alpha(FADE_ALPHA)

    # 時間変数
    t = 0

    running = True
    while running:
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # 画面を完全には消さず、半透明の黒を重ねて残像を作る
        screen.blit(fade_surface, (0, 0))

        # 描画中心
        cx, cy = WIDTH // 2, HEIGHT // 2
        
        # 数理アニメーション描画
        # t（時間）を進める
        t += SPEED_FACTOR

        for i in range(PARTICLE_COUNT):
            # 粒子ごとのインデックス（0.0 〜 1.0）
            idx = i / PARTICLE_COUNT
            
            # 数理モデル: 複数の周期関数の合成
            # 基本となる円運動の角度
            theta = idx * 2 * math.pi
            
            # 半径の変化（呼吸のような動き）
            # sin(t) で全体が収縮・拡大し、sin(theta * n) で花びらのような形を作る
            # 異なる周波数を混ぜることで複雑で有機的な動きにする
            
            wave1 = math.sin(t * 1.5) * 50
            wave2 = math.sin(t * 0.5 + theta * 3) * 100
            wave3 = math.sin(t * 2.3 + theta * 7) * 30
            
            radius = 150 + wave1 + wave2 + wave3
            
            # 極座標 -> 直交座標 変換
            # 少し回転を加えることで渦巻き状にする
            rotation = t * 0.2
            x = cx + radius * math.cos(theta + rotation)
            y = cy + radius * math.sin(theta + rotation)

            # 色の計算 (HSV -> RGB)
            # 時間(t)と粒子の位置(idx)で色を変化させる
            hue = (t * 0.1 + idx * 0.5) % 1.0
            saturation = 0.8
            value = 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            color = (int(r * 255), int(g * 255), int(b * 255))

            # 描画
            # サイズも少し脈動させる
            size = 2 + math.sin(t * 5 + idx * 10) * 1
            pygame.draw.circle(screen, color, (x, y), size)

            # 鏡像（シンメトリー）を描画して万華鏡感を出す（オプション）
            x2 = cx + radius * math.cos(theta + rotation + math.pi)
            y2 = cy + radius * math.sin(theta + rotation + math.pi)
            pygame.draw.circle(screen, color, (x2, y2), size)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()