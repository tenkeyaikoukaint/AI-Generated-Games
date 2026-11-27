import pygame
import math

# --- 設定 ---
WIDTH, HEIGHT = 800, 600
BG_COLOR = (10, 10, 20)
# レトロな緑色の球
BASE_COLOR = (0, 255, 100) 
# 分割数（これを増やすと滑らかになりますが重くなります）
LATITUDE_BANDS = 12  # 緯度方向の分割
LONGITUDE_BANDS = 12 # 経度方向の分割
RADIUS = 200

# 光源ベクトル（正規化済みであること）
# 右上手前から光が来ている設定
LIGHT_DIR = (0.577, -0.577, -0.577) 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Flat Shading Sphere")
clock = pygame.time.Clock()

# --- ベクトル演算関数（NumPyを使わない軽量実装） ---
def rotate_x(x, y, z, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return x, y * c - z * s, y * s + z * c

def rotate_y(x, y, z, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return x * c + z * s, y, -x * s + z * c

def cross_product(v1, v2):
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0]
    )

def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

def normalize(v):
    l = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if l == 0: return (0, 0, 0)
    return (v[0]/l, v[1]/l, v[2]/l)

def subtract(v1, v2):
    return (v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2])

# --- 球のモデルデータを生成（頂点と面） ---
vertices = []
faces = [] # (v1_idx, v2_idx, v3_idx, v4_idx)

# 頂点の生成（球座標系）
for lat in range(LATITUDE_BANDS + 1):
    theta = lat * math.pi / LATITUDE_BANDS
    sin_theta = math.sin(theta)
    cos_theta = math.cos(theta)

    for lon in range(LONGITUDE_BANDS + 1):
        phi = lon * 2 * math.pi / LONGITUDE_BANDS
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)

        x = RADIUS * sin_theta * cos_phi
        y = RADIUS * cos_theta
        z = RADIUS * sin_theta * sin_phi
        vertices.append((x, y, z))

# 面（四角形）の定義
# 隣り合う頂点を結んで面を作る
for lat in range(LATITUDE_BANDS):
    for lon in range(LONGITUDE_BANDS):
        first = (lat * (LONGITUDE_BANDS + 1)) + lon
        second = first + LONGITUDE_BANDS + 1
        
        # 四角形の4頂点のインデックス
        p1 = first
        p2 = second
        p3 = second + 1
        p4 = first + 1
        faces.append((p1, p2, p3, p4))

# --- メインループ ---
running = True
angle_x = 0
angle_y = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)

    # アニメーション用回転角度
    angle_x += 0.01
    angle_y += 0.02

    # 1. すべての頂点を回転させる
    rotated_vertices = []
    for v in vertices:
        rx, ry, rz = rotate_y(v[0], v[1], v[2], angle_y)
        rx, ry, rz = rotate_x(rx, ry, rz, angle_x)
        rotated_vertices.append((rx, ry, rz))

    # 描画するポリゴンのリスト
    polygons_to_draw = []

    # 2. 各面の計算
    for face in faces:
        # 面を構成する頂点座標を取得
        v1 = rotated_vertices[face[0]]
        v2 = rotated_vertices[face[1]]
        v3 = rotated_vertices[face[2]]
        # v4は三角形分割計算には使わないが描画に使う
        v4 = rotated_vertices[face[3]]

        # 面の法線ベクトルを計算 (クロス積)
        # ベクトル A = v2 - v1, ベクトル B = v3 - v1
        vec_a = subtract(v2, v1)
        vec_b = subtract(v3, v1)
        normal = normalize(cross_product(vec_a, vec_b))

        # 【バックフェイスカリング】
        # 法線のZ成分が負（奥を向いている）なら描画しない
        # ※視点は(0,0, -∞)とするか、あるいは単に法線のZを見る簡易判定
        if normal[2] > 0: 
            
            # 【ライティング計算】
            # 法線 と 光源ベクトル の内積（-1.0 〜 1.0）
            # 光源ベクトルは「光が来る方向」か「光へ向かう方向」かで符号注意
            # ここではシンプルに「向きが合うほど明るい」とする
            intensity = dot_product(normal, LIGHT_DIR)
            
            # 環境光(Ambient) + 拡散光(Diffuse)
            # 内積がマイナス（光が当たらない裏側）は0にする
            brightness = max(0.1, intensity) 
            
            # 色の決定
            color = (
                int(BASE_COLOR[0] * brightness),
                int(BASE_COLOR[1] * brightness),
                int(BASE_COLOR[2] * brightness)
            )

            # 透視投影（3D座標 -> 2D画面座標）
            # 簡易的に z を無視してオフセットのみ（平行投影に近い）でもよいが、
            # ここでは単純に画面中央に持ってくる
            points_2d = []
            avg_z = 0
            for v in [v1, v2, v3, v4]:
                # 簡易的な投影: (x + center_x, y + center_y)
                points_2d.append((v[0] + WIDTH // 2, v[1] + HEIGHT // 2))
                avg_z += v[2]
            
            # 面の平均Z座標（ソート用）
            avg_z /= 4

            polygons_to_draw.append((avg_z, color, points_2d))

    # 3. Zソート（奥にある面から順に描画するため）
    # バックフェイスカリングしてるので凸立体なら不要な場合もあるが、
    # 念のためZ値（小さいほうが奥か手前かは座標系による）でソート
    # この座標系ではZ+が手前、Z-が奥になっているので、小さい順（奥から）描画
    polygons_to_draw.sort(key=lambda x: x[0])

    # 4. 描画
    for poly in polygons_to_draw:
        # ポリゴンを塗りつぶし
        pygame.draw.polygon(screen, poly[1], poly[2])
        # ポリゴンの輪郭（ワイヤーフレーム）を少し暗い色で描くとよりレトロ感が出る
        pygame.draw.polygon(screen, (0, 50, 20), poly[2], 1)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()