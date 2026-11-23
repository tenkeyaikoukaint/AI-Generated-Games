import os
import random


WIDTH, HEIGHT = 20, 10


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def create_floor(floor_num):
    # 外周を壁(#)、内側を床(.)にし、ランダムに柱を配置
    grid = [
        [
            "#" if x in (0, WIDTH - 1) or y in (0, HEIGHT - 1) or random.random() < 0.12 else "."
            for x in range(WIDTH)
        ]
        for y in range(HEIGHT)
    ]

    def random_empty():
        while True:
            x, y = random.randint(1, WIDTH - 2), random.randint(1, HEIGHT - 2)
            if grid[y][x] == ".":
                return [x, y]

    player_pos = random_empty()
    stairs = random_empty()
    while stairs == player_pos:
        stairs = random_empty()

    # 階層に応じて敵を配置 [x, y, hp]
    enemies = []
    for _ in range(2 + floor_num):
        pos = random_empty()
        if pos != player_pos and pos != stairs and all(e[:2] != pos for e in enemies):
            enemies.append([pos[0], pos[1], 3 + floor_num])

    # 回復ポーションを配置
    potions = []
    for _ in range(2):
        pos = random_empty()
        if pos != player_pos and pos != stairs and all(e[:2] != pos for e in enemies):
            potions.append(pos)

    return grid, player_pos, stairs, enemies, potions


def main():
    floor = 1
    hp, max_hp, atk = 20, 20, 3
    score = 0
    msg = "ダンジョンへようこそ！階段(>)を目指そう。"

    grid, player, stairs, enemies, potions = create_floor(floor)

    while hp > 0:
        clear()
        print(f"=== TINY ROGUELIKE | B{floor}F | HP: {hp}/{max_hp} | ATK: {atk} | SCORE: {score} ===")

        # マップ描画
        for y in range(HEIGHT):
            row = ""
            for x in range(WIDTH):
                if [x, y] == player:
                    row += "@"
                elif any(e[0] == x and e[1] == y for e in enemies):
                    row += "E"
                elif [x, y] in potions:
                    row += "+"
                elif [x, y] == stairs:
                    row += ">"
                else:
                    row += grid[y][x]
            print(row)

        print(f"\n> {msg}")
        cmd = input("移動 [w/a/s/d] + Enter (終了: q): ").strip().lower()
        if cmd == "q":
            print("ゲームを終了しました。")
            return

        dx, dy = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}.get(cmd, (0, 0))
        if (dx, dy) == (0, 0):
            msg = "w, a, s, d のいずれかを入力してください。"
            continue

        nx, ny = player[0] + dx, player[1] + dy
        msg = ""

        # プレイヤーの行動
        target_enemy = next((e for e in enemies if e[0] == nx and e[1] == ny), None)
        if target_enemy:
            target_enemy[2] -= atk
            if target_enemy[2] <= 0:
                enemies.remove(target_enemy)
                score += 10 * floor
                msg = f"敵を倒した！ (+{10 * floor}点)"
            else:
                msg = f"敵に {atk} ダメージ！(残りHP: {target_enemy[2]})"
        elif grid[ny][nx] == "#":
            msg = "壁にぶつかった。"
        else:
            player = [nx, ny]
            if player in potions:
                potions.remove(player)
                heal = 6
                hp = min(max_hp, hp + heal)
                msg = f"ポーションを飲んだ！ HPが {heal} 回復。"
            elif player == stairs:
                floor += 1
                score += 50
                hp = min(max_hp, hp + 3)
                grid, player, stairs, enemies, potions = create_floor(floor)
                msg = f"B{floor}F に降りた！ (+50点)"
                continue

        # 敵の行動（プレイヤーが近いと追いかけてくる）
        for e in enemies:
            dist = abs(e[0] - player[0]) + abs(e[1] - player[1])
            if dist == 1:
                dmg = random.randint(1, 1 + floor)
                hp -= dmg
                msg += f" 敵の攻撃！ {dmg} ダメージを受けた！"
            elif dist <= 6:
                step_x = 1 if player[0] > e[0] else (-1 if player[0] < e[0] else 0)
                step_y = 1 if player[1] > e[1] else (-1 if player[1] < e[1] else 0)
                ex, ey = (e[0] + step_x, e[1]) if abs(player[0] - e[0]) >= abs(player[1] - e[1]) else (e[0], e[1] + step_y)
                if grid[ey][ex] == "." and [ex, ey] != player and all(o[:2] != [ex, ey] for o in enemies):
                    e[0], e[1] = ex, ey

    clear()
    print(f"GAME OVER... 到達階層: B{floor}F | 最終スコア: {score}")


if __name__ == "__main__":
    main()
