import sys

# ゲームデータ定義
rooms = {
    "玄関ホール": {
        "desc": "薄暗い玄関ホールだ。大きな木製の【玄関の扉】が固く閉ざされている。北にリビング、東に書斎がある。",
        "exits": {"北": "リビング", "東": "書斎"},
        "objects": {
            "玄関の扉": "頑丈な鍵がかかっている。脱出するには【玄関の鍵】が必要だ。",
            "靴箱": "埃をかぶっている。特にめぼしいものはない。"
        },
        "items": []
    },
    "リビング": {
        "desc": "古びたソファと暖炉があるリビングだ。壁には【絵画】が飾られている。南に玄関ホール、西にキッチンがある。",
        "exits": {"南": "玄関ホール", "西": "キッチン"},
        "objects": {
            "絵画": "寂しげな風景画だ。額縁の裏を覗くと、メモが貼ってある。『金庫の番号は、暖炉の薪の数と同じ4桁：1842』",
            "暖炉": "火は消えて冷たくなっている。燃え残った薪が転がっている。"
        },
        "items": ["懐中電灯"]
    },
    "キッチン": {
        "desc": "食器が散乱したキッチンだ。奥の【戸棚】が暗くてよく見えない。東にリビングがある。",
        "exits": {"東": "リビング"},
        "objects": {
            "戸棚": "真っ暗で中が見えない。明かりがあれば調べられそうだ。"
        },
        "items": []
    },
    "書斎": {
        "desc": "本棚が並ぶ静かな書斎だ。机の上に小さな【金庫】が置かれている。西に玄関ホールがある。",
        "exits": {"西": "玄関ホール"},
        "objects": {
            "金庫": "4桁のダイヤル式金庫だ。『使う 金庫』で番号を入力できそうだ。",
            "本棚": "古い洋書がぎっしり詰まっている。"
        },
        "items": []
    }
}

# プレイヤー状態
current_room = "玄関ホール"
inventory = []
flags = {
    "cupboard_lit": False,
    "safe_opened": False
}

def show_status():
    room = rooms[current_room]
    print("\n" + "=" * 45)
    print(f"【現在地: {current_room}】")
    print(room["desc"])
    if room["items"]:
        print(f"落ちているもの: {', '.join(room['items'])}")
    exits_str = ", ".join([f"{direction}({dest})" for direction, dest in room["exits"].items()])
    print(f"移動先: {exits_str}")
    print("=" * 45)

def show_help():
    print("\n--- コマンド一覧 ---")
    print("移動 [方角]   : 指定した方角へ移動する (例: 移動 北)")
    print("調べる [対象] : 部屋にあるものを調べる (例: 調べる 絵画)")
    print("取る [アイテム]: 落ちているアイテムを拾う (例: 取る 懐中電灯)")
    print("使う [対象]   : アイテムや仕掛けを使う (例: 使う 懐中電灯 / 使う 金庫)")
    print("持ち物        : 所持しているアイテムを確認する")
    print("ヘルプ        : この一覧を表示する")
    print("終了          : ゲームを終了する")

def main():
    print("=============================================")
    print("      古びた洋館からの脱出 - Text Adventure")
    print("=============================================")
    print("気がつくと、見知らぬ洋館の玄関に立っていた。")
    print("コマンドを入力して脱出を目指そう。（困ったら「ヘルプ」と入力）")

    global current_room

    while True:
        show_status()
        command_input = input("\n> ").strip()
        if not command_input:
            continue

        parts = command_input.split()
        cmd = parts[0]
        target = parts[1] if len(parts) > 1 else ""

        if cmd == "終了":
            print("ゲームを終了します。")
            sys.exit()

        elif cmd == "ヘルプ":
            show_help()

        elif cmd == "持ち物":
            if inventory:
                print(f"持ち物: {', '.join(inventory)}")
            else:
                print("何も持っていない。")

        elif cmd == "移動":
            if target in rooms[current_room]["exits"]:
                current_room = rooms[current_room]["exits"][target]
                print(f"{current_room}へ移動した。")
            else:
                print("その方向には進めない。（例: 移動 北）")

        elif cmd == "調べる":
            if target in rooms[current_room]["objects"]:
                print(rooms[current_room]["objects"][target])
            else:
                print(f"「{target}」は見当たらない。")

        elif cmd == "取る":
            if target in rooms[current_room]["items"]:
                rooms[current_room]["items"].remove(target)
                inventory.append(target)
                print(f"【{target}】を手に入れた！")
            else:
                print(f"「{target}」はここに落ちていない。")

        elif cmd == "使う":
            # 懐中電灯をキッチンで使う
            if target == "懐中電灯":
                if "懐中電灯" not in inventory:
                    print("懐中電灯を持っていない。")
                elif current_room == "キッチン" and not flags["cupboard_lit"]:
                    flags["cupboard_lit"] = True
                    rooms["キッチン"]["objects"]["戸棚"] = "懐中電灯で照らした。奥にメモが落ちている。『金庫の鍵は書斎にあるが、番号はリビングの絵の裏だ』"
                    print("懐中電灯で戸棚の奥を照らした！何かが見える。戸棚を調べてみよう。")
                else:
                    print("懐中電灯をつけた。あたりが少し明るくなった。")

            # 金庫を調べる・開ける
            elif target == "金庫" and current_room == "書斎":
                if flags["safe_opened"]:
                    print("金庫はすでに空だ。")
                else:
                    code = input("4桁の暗証番号を入力してください: ").strip()
                    if code == "1842":
                        flags["safe_opened"] = True
                        inventory.append("玄関の鍵")
                        print("カチャリ！金庫が開いた。中から【玄関の鍵】を手に入れた！")
                    else:
                        print("番号が違うようだ。")

            # 玄関の鍵を玄関ホールで使う
            elif target == "玄関の鍵":
                if "玄関の鍵" not in inventory:
                    print("玄関の鍵を持っていない。")
                elif current_room == "玄関ホール":
                    print("\n鍵を差し込んで回すと、重い音を立てて扉が開いた！")
                    print("外の冷たい空気が流れ込んでくる……。")
                    print("★★★ 脱出成功！ゲームクリア！ ★★★")
                    break
                else:
                    print("ここでは使えないようだ。")

            else:
                print(f"「{target}」はここでは使えないか、使い方がわからない。")

        else:
            print("そのコマンドは認識できない。「ヘルプ」でコマンドを確認しよう。")

if __name__ == "__main__":
    main()