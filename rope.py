import pygame
import math

# --- 設定 ---
WIDTH, HEIGHT = 800, 600
GRAVITY = 0.5       # 重力
FRICTION = 0.99     # 摩擦（空気抵抗）：1.0だと永久に止まらない
SEGMENT_LENGTH = 15 # 紐の節（ふし）の長さ
NUM_SEGMENTS = 30   # 紐の節の数
CONSTRAINT_ITERATIONS = 5 # 紐の「硬さ」を決める計算回数（多いほど伸びない）

# --- 色 ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

class Point:
    def __init__(self, x, y, locked=False):
        self.x = x
        self.y = y
        self.old_x = x # 1フレーム前の位置（これが速度代わりになる）
        self.old_y = y
        self.locked = locked # 固定点かどうか

    def update(self):
        if self.locked:
            return

        # --- 1. ベルレ積分 (Verlet Integration) ---
        # 速度変数を使わず、「差分」で慣性を表現する魔法
        vx = (self.x - self.old_x) * FRICTION
        vy = (self.y - self.old_y) * FRICTION

        # 現在位置を「過去」として保存
        self.old_x = self.x
        self.old_y = self.y

        # 新しい位置 = 現在位置 + 慣性(速度) + 重力
        self.x += vx
        self.y += vy + GRAVITY

        # --- 画面外に出ないようにする（簡易衝突） ---
        if self.y > HEIGHT:
            self.y = HEIGHT
            self.old_y = self.y + vy * 0.5 # 地面で少しバウンドさせるトリック

class Stick:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.length = SEGMENT_LENGTH

    def update(self):
        # --- 2. 距離の拘束 (Distance Constraint) ---
        # 2つの点の距離を測る
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # ゼロ除算防止
        if distance == 0: 
            return

        # 「あるべき長さ」とのズレ（誤差）
        difference = self.length - distance
        percent = difference / distance / 2.0
        
        # ズレた分だけ、お互いを引っ張り合う（または押し合う）
        offset_x = dx * percent
        offset_y = dy * percent

        if not self.p1.locked:
            self.p1.x -= offset_x
            self.p1.y -= offset_y
        
        if not self.p2.locked:
            self.p2.x += offset_x
            self.p2.y += offset_y

    def draw(self, screen):
        pygame.draw.line(screen, WHITE, (self.p1.x, self.p1.y), (self.p2.x, self.p2.y), 2)

# --- メインループ ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # 紐の生成：点(Point)と棒(Stick)を作る
    points = []
    sticks = []
    
    start_x = WIDTH // 2
    start_y = 50
    
    for i in range(NUM_SEGMENTS):
        # 最初の点だけ固定する(locked=True)
        locked = (i == 0)
        p = Point(start_x, start_y + i * SEGMENT_LENGTH, locked)
        points.append(p)
        
        if i > 0:
            s = Stick(points[i-1], points[i])
            sticks.append(s)

    running = True
    while running:
        screen.fill(BLACK)
        
        # 入力処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # クリック中は最初の点をマウス位置に強制移動
                points[0].locked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                # 離しても固定したままにする（お好みでFalseにしてもよい）
                pass

        # マウス操作
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            points[0].x = mx
            points[0].y = my

        # --- 物理更新 ---
        # 1. 全ての点に重力をかける
        for p in points:
            p.update()

        # 2. 拘束を解決する（数回繰り返すと紐が硬くなる）
        for _ in range(CONSTRAINT_ITERATIONS):
            for s in sticks:
                s.update()

        # --- 描画 ---
        for s in sticks:
            s.draw(screen)
        
        # 点も描きたければコメントアウトを外す
        # for p in points:
        #     pygame.draw.circle(screen, GRAY, (int(p.x), int(p.y)), 3)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()