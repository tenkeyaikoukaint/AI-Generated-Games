import random

class Minesweeper:
    def __init__(self, width=9, height=9, mines=10):
        self.width = width
        self.height = height
        self.mines_count = mines
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        self.visible = [[False for _ in range(width)] for _ in range(height)]
        self.flagged = [[False for _ in range(width)] for _ in range(height)]
        self.first_move = True
        self.game_over = False
        self.win = False

    def place_mines(self, safe_r, safe_c):
        # 最初の1手目とその周囲8マスには地雷を置かない
        forbidden = {
            (r, c)
            for r in range(max(0, safe_r - 1), min(self.height, safe_r + 2))
            for c in range(max(0, safe_c - 1), min(self.width, safe_c + 2))
        }
        candidates = [
            (r, c)
            for r in range(self.height)
            for c in range(self.width)
            if (r, c) not in forbidden
        ]
        for r, c in random.sample(candidates, self.mines_count):
            self.board[r][c] = -1  # -1 を地雷とする

        # 各マスの周囲の地雷数を計算
        for r in range(self.height):
            for c in range(self.width):
                if self.board[r][c] == -1:
                    continue
                count = 0
                for nr in range(max(0, r - 1), min(self.height, r + 2)):
                    for nc in range(max(0, c - 1), min(self.width, c + 2)):
                        if self.board[nr][nc] == -1:
                            count += 1
                self.board[r][c] = count

    def open_cell(self, r, c):
        if not (0 <= r < self.height and 0 <= c < self.width):
            return
        if self.visible[r][c] or self.flagged[r][c]:
            return

        if self.first_move:
            self.place_mines(r, c)
            self.first_move = False

        self.visible[r][c] = True

        if self.board[r][c] == -1:
            self.game_over = True
            return

        # 周囲に地雷がない(0)場合は隣接マスを連鎖的に開く
        if self.board[r][c] == 0:
            for nr in range(max(0, r - 1), min(self.height, r + 2)):
                for nc in range(max(0, c - 1), min(self.width, c + 2)):
                    if not self.visible[nr][nc]:
                        self.open_cell(nr, nc)

    def toggle_flag(self, r, c):
        if 0 <= r < self.height and 0 <= c < self.width and not self.visible[r][c]:
            self.flagged[r][c] = not self.flagged[r][c]

    def check_win(self):
        for r in range(self.height):
            for c in range(self.width):
                if self.board[r][c] != -1 and not self.visible[r][c]:
                    return False
        self.win = True
        self.game_over = True
        return True

    def display(self, reveal_all=False):
        cols = " ".join(chr(ord('A') + c) for c in range(self.width))
        print(f"\n   {cols}")
        print("  +" + "-" * (self.width * 2 - 1) + "+")
        for r in range(self.height):
            row_str = []
            for c in range(self.width):
                if reveal_all and self.board[r][c] == -1:
                    row_str.append("*")
                elif self.flagged[r][c]:
                    row_str.append("F")
                elif not self.visible[r][c]:
                    row_str.append(".")
                elif self.board[r][c] == 0:
                    row_str.append(" ")
                else:
                    row_str.append(str(self.board[r][c]))
            print(f"{r + 1:2}|{' '.join(row_str)}|")
        print("  +" + "-" * (self.width * 2 - 1) + "+")

def main():
    game = Minesweeper(width=9, height=9, mines=10)
    print("コマンド例: 'o A1' (開く), 'f B3' (旗), 'q' (終了)")

    while not game.game_over:
        game.display()
        cmd = input("入力 > ").strip().split()
        if not cmd:
            continue
        if cmd[0].lower() == 'q':
            break
        if len(cmd) != 2 or len(cmd[1]) < 2:
            print("形式エラー: 'o A1' または 'f A1' のように入力してください。")
            continue

        action = cmd[0].lower()
        col_char = cmd[1][0].upper()
        try:
            c = ord(col_char) - ord('A')
            r = int(cmd[1][1:]) - 1
        except ValueError:
            print("座標の指定が不正です。")
            continue

        if action == 'o':
            game.open_cell(r, c)
            if not game.game_over:
                game.check_win()
        elif action == 'f':
            game.toggle_flag(r, c)
        else:
            print("'o' (開く) か 'f' (旗) を指定してください。")

    game.display(reveal_all=True)
    if game.win:
        print("クリア！すべての地雷を特定しました。")
    elif game.game_over:
        print("BOOM! 地雷を踏みました。")

if __name__ == "__main__":
    main()
