import sys

# マップデータ（全8部屋・3階層）
rooms = {
    "玄関ホール": {
        "floor": "1F",
        "desc": "薄暗い玄関ホールだ。大きな【玄関の扉】には太い鎖が巻かれ、頑丈な鍵もかかっている。上に2階への階段がある。",
        "exits": {"北": "リビング", "東": "書斎", "上": "2階廊下"},
        "objects": {
            "玄関の扉": "太い鎖と鍵穴がある。脱出するには鎖を切る道具と【玄関の鍵】の両方が必要だ。",
            "靴箱": "埃をかぶった古い革靴が並んでいる。特にめぼしいものはない。"
        },
        "items": []
    },
    "リビング": {
        "floor": "1F",
        "desc": "広いリビングだ。中央にテーブルと【椅子】が並び、壁には古びた【絵画】が飾られている。",
        "exits": {"南": "玄関ホール", "西": "キッチン"},
        "objects": {
            "椅子": "立派な木製の椅子がテーブルを囲むように【4脚】並んでいる。",
            "絵画": "額縁の裏にメモが貼ってある。『金庫の1〜2桁目は書斎の時計の「時」、3桁目はリビングの椅子の数、4桁目は地下室のワイン樽の数』",
            "暖炉": "火は消えている。灰が積もっているだけだ。"
        },
        "items": []
    },
    "キッチン": {
        "floor": "1F",
        "desc": "食器が散乱したキッチンだ。足元に【地下室への扉】があり、壁際には【棚】がある。",
        "exits": {"東": "リビング"},  # 地下室の鍵を使うと「下: 地下室」が追加される
        "objects": {
            "地下室への扉": "重い鉄の扉だ。鍵がかかっていて開かない。",
            "棚": "食器や調理器具が入っている。奥の方を調べると何か光るものがある。"
        },
        "items": []
    },
    "書斎": {
        "floor": "1F",
        "desc": "本棚が並ぶ静かな書斎だ。壁に【掛け時計】があり、立派な【机】の横に【金庫】が置かれている。",
        "exits": {"西": "玄関ホール"},
        "objects": {
            "掛け時計": "針が【07時15分】で完全に止まっている。",
            "机": "引き出しに小さな鍵穴がついている。何か小さな鍵で開きそうだ。",
            "金庫": "4桁のダイヤル式金庫だ。『使う 金庫』で番号を入力できる。"
        },
        "items": []
    },
    "2階廊下": {
        "floor": "2F",
        "desc": "歩くたびに床が軋む2階の廊下だ。北に寝室、東に子供部屋、下に1階への階段がある。",
        "exits": {"下": "玄関ホール", "北": "寝室", "東": "子供部屋"},
        "objects": {
            "窓": "外は深い霧に包まれていて何も見えない。"
        },
        "items": []
    },
    "寝室": {
        "floor": "2F",
        "desc": "大きなベッドがある寝室だ。枕元の【サイドテーブル】の上に【日記】が置かれている。",
        "exits": {"南": "2階廊下"},
        "objects": {
            "サイドテーブル": "引き出しは空だが、上に壊れかけた懐中電灯が置かれている。",
            "日記": "『地下室は真っ暗で危険だ。明かりを持たずに入ってはいけない。電池はキッチンにしまったはずだ』と書かれている。"
        },
        "items": ["懐中電灯（電池切れ）"]
    },
    "子供部屋": {
        "floor": "2F",
        "desc": "色褪せた壁紙の子供部屋だ。部屋の隅に【おもちゃ箱】と【ベッド】がある。",
        "exits": {"西": "2階廊下"},
        "objects": {
            "おもちゃ箱": "古いぬいぐるみや積み木が入っている。底の方に小さな鍵が落ちているのを見つけた！",
            "ベッド": "小さなベッドだ。シーツの下には何もない。"
        },
        "items": []
    },
    "地下室": {
        "floor": "B1",
        "desc": "真っ暗で何も見えない……！明かりがないと探索できそうにない。",
        "exits": {"上": "キッチン"},
        "objects": {},
        "items": []
    }
}

# プレイヤー状態とフラグ
current_room = "玄関ホール"
inventory = []
turns = 0
flags = {
    "battery_found": False,
    "small_key_found": False,
    "desk_unlocked": False,
    "basement_unlocked": False,
    "basement_lit": False,
    "cutter_found": False,
    "safe_opened": False,
    "chain_cut": False
}

def show_map():
    print("\n--- 洋館マップ ---")
    print("[2F]  寝室")
    print("       |")
    print("     2階廊下 ── 子供部屋")
    print("       | (階段)")
    print("[1F] キッチン ── リビング")
    print("       | (地下)     |")
    print("     [B1]地下室   玄関ホール ── 書斎")
    print(f"※現在地: {current_room} ({rooms[current_room]['floor']})")

def show_status():
    room = rooms[current_room]
    print("\n" + "=" * 50)
    print(f"【現在地: {current_room} ({room['floor']})】  ターン数: {turns}")
    print(room["desc"])
    if room["items"]:
        print(f"落ちているもの: {', '.join(room['items'])}")
    exits_str = ", ".join([f"{d}({dest})" for d, dest in room["exits"].items()])
    print(f"移動先: {exits_str}")
    print("=" * 50)

def show_help():
    print("\n--- コマンド一覧 ---")
    print("移動 [方角]               : 指定した方角へ移動 (北/南/東/西/上/下)")
    print("調べる [対象]             : 部屋にあるものを調べる (例: 調べる 絵画)")
    print("取る [アイテム]           : 落ちているアイテムを拾う (例: 取る 乾電池)")
    print("使う [対象]               : アイテムや仕掛けを使う (例: 使う 金庫)")
    print("組み合わせる [物1] [物2]  : 2つのアイテムを組み合わせる")
    print("持ち物                    : 所持しているアイテムを確認")
    print("マップ                    : 洋館の見取り図を表示")
    print("ヘルプ                    : この一覧を表示")
    print("終了                      : ゲームを終了")

def main():
    global current_room, turns

    print("==================================================")
    print("    古びた洋館からの脱出 Ver.2 - Text Adventure")
    print("==================================================")
    print("気がつくと、見知らぬ洋館の玄関に立っていた。")
    print("3階層の館を探索し、謎を解いて脱出しよう。（困ったら「ヘルプ」）")

    while True:
        show_status()
        command_input = input("\n> ").strip()
        if not command_input:
            continue

        parts = command_input.split()
        cmd = parts[0]
        arg1 = parts[1] if len(parts) > 1 else ""
        arg2 = parts[2] if len(parts) > 2 else ""

        if cmd == "終了":
            print("ゲームを終了します。")
            sys.exit()

        elif cmd == "ヘルプ":
            show_help()
            continue

        elif cmd == "マップ":
            show_map()
            continue

        elif cmd == "持ち物":
            print(f"持ち物: {', '.join(inventory)}" if inventory else "何も持っていない。")
            continue

        # 行動系コマンドはターンを消費
        turns += 1

        if cmd == "移動":
            if arg1 in rooms[current_room]["exits"]:
                current_room = rooms[current_room]["exits"][arg1]
                print(f"{current_room}へ移動した。")
            else:
                print("その方向には進めない。")
                turns -= 1

        elif cmd == "調べる":
            room = rooms[current_room]
            if current_room == "地下室" and not flags["basement_lit"]:
                print("真っ暗で何も見えない。明かりが必要だ。")
                continue

            if arg1 in room["objects"]:
                print(room["objects"][arg1])
                # 調べることで発生するイベント
                if current_room == "キッチン" and arg1 == "棚" and not flags["battery_found"]:
                    flags["battery_found"] = True
                    room["items"].append("乾電池")
                    room["objects"]["棚"] = "食器や調理器具が並んでいる。もう目ぼしいものはない。"
                    print("→ 棚の奥から【乾電池】を見つけた！（「取る 乾電池」で拾えます）")

                elif current_room == "子供部屋" and arg1 == "おもちゃ箱" and not flags["small_key_found"]:
                    flags["small_key_found"] = True
                    room["items"].append("小さな鍵")
                    room["objects"]["おもちゃ箱"] = "古いぬいぐるみや積み木が入っている。"
                    print("→ おもちゃ箱の底に【小さな鍵】がある！（「取る 小さな鍵」で拾えます）")

                elif current_room == "地下室" and arg1 == "工具棚" and not flags["cutter_found"]:
                    flags["cutter_found"] = True
                    room["items"].append("ボルトカッター")
                    room["objects"]["工具棚"] = "錆びた工具が並んでいる。"
                    print("→ 頑丈な【ボルトカッター】を見つけた！（「取る ボルトカッター」で拾えます）")
            else:
                print(f"「{arg1}」は見当たらない。")

        elif cmd == "取る":
            if current_room == "地下室" and not flags["basement_lit"]:
                print("暗くて手探りでは拾えない。")
                continue

            if arg1 in rooms[current_room]["items"]:
                rooms[current_room]["items"].remove(arg1)
                inventory.append(arg1)
                print(f"【{arg1}】を手に入れた！")
            else:
                print(f"「{arg1}」はここに落ちていない。")

        elif cmd == "組み合わせる":
            pair = {arg1, arg2}
            if pair == {"懐中電灯（電池切れ）", "乾電池"}:
                if "懐中電灯（電池切れ）" in inventory and "乾電池" in inventory:
                    inventory.remove("懐中電灯（電池切れ）")
                    inventory.remove("乾電池")
                    inventory.append("懐中電灯")
                    print("懐中電灯に乾電池を入れた！明かりがつく【懐中電灯】が完成した！")
                else:
                    print("必要なアイテムが揃っていない。")
            else:
                print("その組み合わせでは何も起きないようだ。")

        elif cmd == "使う":
            # 小さな鍵を書斎の机に使う
            if arg1 == "小さな鍵":
                if "小さな鍵" not in inventory:
                    print("小さな鍵を持っていない。")
                elif current_room == "書斎" and not flags["desk_unlocked"]:
                    flags["desk_unlocked"] = True
                    inventory.remove("小さな鍵")
                    inventory.append("地下室の鍵")
                    rooms["書斎"]["objects"]["机"] = "引き出しはすでに開いている。中は空だ。"
                    print("カチャリ！机の引き出しが開き、中から【地下室の鍵】を手に入れた！")
                else:
                    print("ここでは使えないようだ。")

            # 地下室の鍵をキッチンで使う
            elif arg1 == "地下室の鍵":
                if "地下室の鍵" not in inventory:
                    print("地下室の鍵を持っていない。")
                elif current_room == "キッチン" and not flags["basement_unlocked"]:
                    flags["basement_unlocked"] = True
                    inventory.remove("地下室の鍵")
                    rooms["キッチン"]["exits"]["下"] = "地下室"
                    rooms["キッチン"]["objects"]["地下室への扉"] = "鍵は開いている。地下室へ降りられる。"
                    print("重い鍵が開いた！キッチンから下（地下室）へ移動できるようになった。")
                else:
                    print("ここでは使えないようだ。")

            # 懐中電灯を地下室で使う
            elif arg1 == "懐中電灯":
                if "懐中電灯" not in inventory:
                    print("使える懐中電灯を持っていない。")
                elif current_room == "地下室" and not flags["basement_lit"]:
                    flags["basement_lit"] = True
                    rooms["地下室"]["desc"] = "懐中電灯の光で照らされた地下室だ。壁際に【ワイン樽】が並び、奥に【工具棚】がある。"
                    rooms["地下室"]["objects"] = {
                        "ワイン樽": "埃をかぶった大きなワイン樽が【3つ】並んでいる。",
                        "工具棚": "錆びた工具が雑多に置かれている。奥に大きな切断工具が見える。"
                    }
                    print("懐中電灯をつけた！地下室の様子がはっきり見えるようになった。")
                else:
                    print("懐中電灯で周囲を照らしたが、特に変わったものはない。")

            # 金庫を書斎で開ける
            elif arg1 == "金庫" and current_room == "書斎":
                if flags["safe_opened"]:
                    print("金庫はすでに空だ。")
                else:
                    code = input("4桁の暗証番号を入力してください: ").strip()
                    if code == "0743":
                        flags["safe_opened"] = True
                        inventory.append("玄関の鍵")
                        print("ガチャン！金庫が開いた！中から【玄関の鍵】を手に入れた！")
                    else:
                        print("番号が違うようだ……。（ヒントはリビングの絵画の裏にある）")

            # ボルトカッターを玄関ホールで使う
            elif arg1 == "ボルトカッター":
                if "ボルトカッター" not in inventory:
                    print("ボルトカッターを持っていない。")
                elif current_room == "玄関ホール" and not flags["chain_cut"]:
                    flags["chain_cut"] = True
                    rooms["玄関ホール"]["objects"]["玄関の扉"] = "鎖は切断した。あとは【玄関の鍵】で開けるだけだ。"
                    print("ガキンッ！玄関の扉に巻かれていた太い鎖を切断した！")
                else:
                    print("ここでは使えないようだ。")

            # 玄関の鍵を玄関ホールで使う
            elif arg1 == "玄関の鍵":
                if "玄関の鍵" not in inventory:
                    print("玄関の鍵を持っていない。")
                elif current_room == "玄関ホール":
                    if not flags["chain_cut"]:
                        print("鍵は開いたが、まだ太い鎖が巻かれていて扉が開かない！鎖を切る道具が必要だ。")
                    else:
                        print("\n鍵を回し、鎖の外れた重い扉を押し開けた！")
                        print("朝の光が差し込み、冷たい外気が頬を撫でる……。")
                        print("==================================================")
                        print("        ★★★ 脱出成功！ゲームクリア！ ★★★")
                        print(f"        クリアターン数: {turns} ターン")
                        rank = "S" if turns <= 25 else "A" if turns <= 35 else "B" if turns <= 50 else "C"
                        print(f"        探索ランク: {rank}")
                        print("==================================================")
                        break
                else:
                    print("ここでは使えないようだ。")

            else:
                print(f"「{arg1}」はここでは使えないか、使い方がわからない。")

        else:
            print("そのコマンドは認識できない。「ヘルプ」で確認しよう。")
            turns -= 1

if __name__ == "__main__":
    main()