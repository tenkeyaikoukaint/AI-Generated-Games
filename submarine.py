import math
import random


def get_direction(dx, dy):
    if dx == 0 and dy == 0:
        return "直下"
    angle = math.degrees(math.atan2(dy, dx))
    if -22.5 <= angle < 22.5:
        return "東 (E)"
    elif 22.5 <= angle < 67.5:
        return "北東 (NE)"
    elif 67.5 <= angle < 112.5:
        return "北 (N)"
    elif 112.5 <= angle < 157.5:
        return "北西 (NW)"
    elif angle >= 157.5 or angle < -157.5:
        return "西 (W)"
    elif -157.5 <= angle < -112.5:
        return "南西 (SW)"
    elif -112.5 <= angle < -67.5:
        return "南 (S)"
    else:
        return "南東 (SE)"


def main():
    GRID_SIZE = 10
    px, py = GRID_SIZE // 2, GRID_SIZE // 2  # 自艦の初期位置 (5, 5)
    ex, ey = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
    while (ex, ey) == (px, py):
        ex, ey = random.randint(0, GRID_SIZE - 1), random.randint(
            0, GRID_SIZE - 1
        )

    torpedoes = 5
    fuel = 15
    turn = 1

    print("=== SILENT DEPTH (CLI潜水艦戦) ===")
    print(f"海域: {GRID_SIZE}x{GRID_SIZE} (0〜{GRID_SIZE-1})")
    print("目標: ソナーで敵艦を特定し、魚雷で撃沈せよ。\n")

    while True:
        print(f"--- ターン {turn} ---")
        print(f"現在位置: ({px}, {py}) | 残り魚雷: {torpedoes} | 残り燃料: {fuel}")
        print(
            "コマンド: [m]移動(燃料-1) / [p]アクティブソナー(敵に察知される) / [f]魚雷発射 / [w]待機 / [q]終了"
        )

        cmd = input("> ").strip().lower()
        enemy_alerted = False

        if cmd == "q":
            print("作戦を中止しました。")
            break

        elif cmd == "m":
            if fuel <= 0:
                print("燃料切れで移動できません！")
                continue
            d = input("移動方向 (n:北 / s:南 / e:東 / w:西): ").strip().lower()
            nx, ny = px, py
            if d == "n":
                ny += 1
            elif d == "s":
                ny -= 1
            elif d == "e":
                nx += 1
            elif d == "w":
                nx -= 1
            else:
                print("無効な方向です。")
                continue

            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                px, py = nx, ny
                fuel -= 1
                print(f"スクリュー音を抑えつつ ({px}, {py}) へ移動しました。")
            else:
                print("海域の境界です。これ以上進めません。")
                continue

        elif cmd == "p":
            dist = math.hypot(ex - px, ey - py)
            direction = get_direction(ex - px, ey - py)
            noise = random.uniform(-0.8, 0.8)  # わずかな測定誤差
            print(
                f"[ソナー反応] 方位: {direction} / 推定距離: 約 {max(0.0, dist + noise):.1f}"
            )
            enemy_alerted = True  # パッシブではなくアクティブなので位置がバレる

        elif cmd == "f":
            if torpedoes <= 0:
                print("魚雷が残っていません！")
                continue
            try:
                tx = int(input(f"目標 X座標 (0〜{GRID_SIZE-1}): "))
                ty = int(input(f"目標 Y座標 (0〜{GRID_SIZE-1}): "))
            except ValueError:
                print("数値を入力してください。")
                continue

            torpedoes -= 1
            print(f"魚雷発射！ 目標座標 ({tx}, {ty}) へ向かいます...")
            hit_dist = math.hypot(ex - tx, ey - ty)

            if hit_dist == 0:
                print("\n★ 命中！ 敵潜水艦を撃沈しました！作戦成功！ ★")
                break
            elif hit_dist <= 1.5:
                print("至近弾！ 敵艦に損傷を与えた模様。敵は緊急回避行動をとります！")
                enemy_alerted = True
            else:
                print("外れ... 水中爆発音のみが響きました。")
                enemy_alerted = True

            if torpedoes == 0:
                print("\n魚雷をすべて使い切りました。作戦失敗（帰投します）...")
                break

        elif cmd == "w":
            # 待機中はパッシブソナー（聴音）で微かな音だけを拾う
            dist = math.hypot(ex - px, ey - py)
            if dist <= 3.0:
                print("[聴音] 非常に近い位置でスクリュー音を検知しました。")
            elif dist <= 6.0:
                print("[聴音] 遠方で微かな機関音を検知しました。")
            else:
                print("[聴音] 静寂... 異常なし。")

        else:
            print("不明なコマンドです。")
            continue

        # 敵のターン処理
        if enemy_alerted:
            # 察知された場合、敵が1〜2マス移動する
            move_steps = random.choice([1, 2])
            for _ in range(move_steps):
                ex = max(0, min(GRID_SIZE - 1, ex + random.choice([-1, 0, 1])))
                ey = max(0, min(GRID_SIZE - 1, ey + random.choice([-1, 0, 1])))
            print("（※ こちらの動きを察知した敵艦が移動した気配があります）")
        else:
            # 通常時もたまにゆっくり移動する
            if random.random() < 0.3:
                ex = max(0, min(GRID_SIZE - 1, ex + random.choice([-1, 0, 1])))
                ey = max(0, min(GRID_SIZE - 1, ey + random.choice([-1, 0, 1])))

        # 接触判定（敵と重なった場合）
        if (px, py) == (ex, ey):
            print("\n警告：敵艦と至近距離で遭遇！ 先制攻撃を受け撃沈されました...")
            break

        turn += 1
        print()


if __name__ == "__main__":
    main()
