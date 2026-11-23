import copy
import sys
import time

# --- 設定 ---
EMPTY = 0
BLACK = 1  # 先手 (人間)
WHITE = 2  # 後手 (AI)
SEARCH_DEPTH = 4  # AIの思考の深さ（4〜5が快適かつそこそこ強い）

# 8方向ベクトル
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

# 盤面の位置評価テーブル（角は高く、X打ち・C打ちは極端に低い）
WEIGHT_MATRIX = [
    [ 120, -20,  20,   5,   5,  20, -20, 120],
    [ -20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [  20,  -5,  15,   3,   3,  15,  -5,  20],
    [   5,  -5,   3,   3,   3,   3,  -5,   5],
    [   5,  -5,   3,   3,   3,   3,  -5,   5],
    [  20,  -5,  15,   3,   3,  15,  -5,  20],
    [ -20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 120, -20,  20,   5,   5,  20, -20, 120]
]


class Othello:
    def __init__(self):
        self.board = [[EMPTY] * 8 for _ in range(8)]
        self.board[3][3] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.board[4][4] = WHITE

    def print_board(self, valid_moves=None):
        """盤面をCLIに見やすく表示する"""
        if valid_moves is None:
            valid_moves = []
        valid_set = set(valid_moves)

        print("\n    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        for r in range(8):
            row_str = f"{r + 1} |"
            for c in range(8):
                cell = self.board[r][c]
                if cell == BLACK:
                    char = " ● "
                elif cell == WHITE:
                    char = " ○ "
                elif (r, c) in valid_set:
                    char = " · "  # 打てる場所のガイド
                else:
                    char = "   "
                row_str += char + "|"
            print(row_str)
            print("  +---+---+---+---+---+---+---+---+")

        b_count, w_count = self.count_stones()
        print(f"  黒(あなた): {b_count}  |  白(AI): {w_count}\n")

    def count_stones(self):
        b = sum(row.count(BLACK) for row in self.board)
        w = sum(row.count(WHITE) for row in self.board)
        return b, w

    def get_flippable_stones(self, r, c, player):
        """(r, c)にplayerが打った場合に裏返せる石のリストを返す"""
        if self.board[r][c] != EMPTY:
            return []

        opponent = WHITE if player == BLACK else BLACK
        flippable = []

        for dr, dc in DIRECTIONS:
            temp = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == opponent:
                temp.append((nr, nc))
                nr += dr
                nc += dc
            if temp and 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == player:
                flippable.extend(temp)

        return flippable

    def get_valid_moves(self, player):
        """合法手のリスト [(r, c), ...] を返す"""
        moves = []
        for r in range(8):
            for c in range(8):
                if self.get_flippable_stones(r, c, player):
                    moves.append((r, c))
        return moves

    def make_move(self, r, c, player):
        """石を置いて裏返す"""
        flippable = self.get_flippable_stones(r, c, player)
        if not flippable:
            return False
        self.board[r][c] = player
        for fr, fc in flippable:
            self.board[fr][fc] = player
        return True

    def is_game_over(self):
        return not self.get_valid_moves(BLACK) and not self.get_valid_moves(WHITE)

    def evaluate(self, ai_player):
        """盤面の評価関数（位置の重み + 終盤の石数 + 着手可能数）"""
        human_player = WHITE if ai_player == BLACK else BLACK
        b_count, w_count = self.count_stones()
        total_stones = b_count + w_count

        # 終盤（残り12マス以下）は石の数そのものを重視（完全読みに近い挙動）
        if total_stones >= 52:
            ai_stones = w_count if ai_player == WHITE else b_count
            hu_stones = b_count if ai_player == WHITE else w_count
            return (ai_stones - hu_stones) * 100

        # 序盤〜中盤は位置の重みと打てる場所の多さ（開放度・着手可能数）を重視
        pos_score = 0
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == ai_player:
                    pos_score += WEIGHT_MATRIX[r][c]
                elif self.board[r][c] == human_player:
                    pos_score -= WEIGHT_MATRIX[r][c]

        ai_mobility = len(self.get_valid_moves(ai_player))
        hu_mobility = len(self.get_valid_moves(human_player))
        mobility_score = (ai_mobility - hu_mobility) * 10

        return pos_score + mobility_score

    def minimax(self, depth, alpha, beta, maximizing_player, ai_player):
        """α-β法による先読み探索"""
        human_player = WHITE if ai_player == BLACK else BLACK

        if depth == 0 or self.is_game_over():
            return self.evaluate(ai_player), None

        current_player = ai_player if maximizing_player else human_player
        valid_moves = self.get_valid_moves(current_player)

        # パスの場合
        if not valid_moves:
            score, _ = self.minimax(depth - 1, alpha, beta, not maximizing_player, ai_player)
            return score, None

        # 重みが高い順にソートして枝刈り効率を上げる（Move Ordering）
        valid_moves.sort(key=lambda m: WEIGHT_MATRIX[m[0]][m[1]], reverse=True)

        best_move = valid_moves[0]

        if maximizing_player:
            max_eval = -float('inf')
            for r, c in valid_moves:
                next_game = copy.deepcopy(self)
                next_game.make_move(r, c, current_player)
                eval_score, _ = next_game.minimax(depth - 1, alpha, beta, False, ai_player)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (r, c)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for r, c in valid_moves:
                next_game = copy.deepcopy(self)
                next_game.make_move(r, c, current_player)
                eval_score, _ = next_game.minimax(depth - 1, alpha, beta, True, ai_player)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (r, c)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move


def parse_input(user_input):
    """'d3' や '3d' のような入力を (row, col) に変換"""
    s = user_input.strip().lower()
    if len(s) != 2:
        return None
    if s[0] in "abcdefgh" and s[1] in "12345678":
        return int(s[1]) - 1, ord(s[0]) - ord('a')
    if s[1] in "abcdefgh" and s[0] in "12345678":
        return int(s[0]) - 1, ord(s[1]) - ord('a')
    return None


def main():
    game = Othello()
    turn = BLACK

    print("=== Python CLI オセロ ===")
    print("あなたは 黒(●)、AIは 白(○) です。")
    print("座標を 'd3' のように入力してください（終了は 'q'）。")

    while not game.is_game_over():
        valid_moves = game.get_valid_moves(turn)

        if turn == BLACK:
            game.print_board(valid_moves)
            if not valid_moves:
                print("打てる場所がありません。パスします。")
                turn = WHITE
                time.sleep(1)
                continue

            while True:
                move_str = input("あなたの手番 (例: d3) > ")
                if move_str.strip().lower() in ('q', 'quit', 'exit'):
                    print("ゲームを終了します。")
                    sys.exit()

                pos = parse_input(move_str)
                if pos and pos in valid_moves:
                    game.make_move(pos[0], pos[1], BLACK)
                    break
                else:
                    print("無効な手です。'·' の場所に座標を指定してください。")
            turn = WHITE

        else:
            game.print_board()
            if not valid_moves:
                print("AIは打てる場所がありません。パスします。")
                turn = BLACK
                time.sleep(1)
                continue

            print("AIが思考中...", end="", flush=True)
            start_time = time.time()
            _, best_move = game.minimax(SEARCH_DEPTH, -float('inf'), float('inf'), True, WHITE)
            elapsed = time.time() - start_time

            r, c = best_move
            game.make_move(r, c, WHITE)
            coord_str = f"{chr(c + ord('a'))}{r + 1}"
            print(f"\rAIは {coord_str} に打ちました ({elapsed:.2f}秒)")
            turn = BLACK

    # ゲーム終了
    game.print_board()
    b_count, w_count = game.count_stones()
    print("=== ゲーム終了 ===")
    if b_count > w_count:
        print(f"あなたの勝ちです！ ({b_count} 対 {w_count})")
    elif w_count > b_count:
        print(f"AIの勝ちです！ ({w_count} 対 {b_count})")
    else:
        print(f"引き分けです！ ({b_count} 対 {w_count})")


if __name__ == "__main__":
    main()