#!/usr/bin/env python3
"""
THE DEEP CAVERN - 忘れられた鉱脈の奥底
Python 3 標準ライブラリのみ / 日本語メッセージ・英語コマンド入力
"""

import sys

# ---------------------------------------------------------------------------
# データ定義
# ---------------------------------------------------------------------------

ITEMS = {
    "lantern": {
        "name": "オイルランタン",
        "aliases": ["lantern", "lamp"],
        "desc": "真鍮製の古いランタン。暗闇を照らすには火を点ける必要がある。",
    },
    "matches": {
        "name": "防水マッチ",
        "aliases": ["matches", "match"],
        "desc": "湿気に強いマッチ箱。まだ十分に本数が残っている。",
    },
    "crowbar": {
        "name": "鉄のバール",
        "aliases": ["crowbar", "bar"],
        "desc": "ずっしりと重い鉄製のバール。頑丈な蓋をこじ開けられそうだ。",
    },
    "note": {
        "name": "作業員のメモ",
        "aliases": ["note", "memo", "paper"],
        "desc": "くしゃくしゃになった紙切れ。何か文字が書かれている。",
    },
    "rope": {
        "name": "丈夫なロープ",
        "aliases": ["rope"],
        "desc": "太く編まれた麻のロープ。深い崖を降りるのに使えそうだ。",
    },
    "gear": {
        "name": "真鍮の歯車",
        "aliases": ["gear", "cog"],
        "desc": "精巧に刻まれた金属の歯車。何かの機械の一部らしい。",
    },
    "oil1": {
        "name": "予備のオイル缶",
        "aliases": ["oil", "can", "oil1"],
        "desc": "ランタン用の灯油が入った小さな缶。使えば燃料を補給できる。",
    },
    "oil2": {
        "name": "古びたオイル缶",
        "aliases": ["oil", "can", "oil2"],
        "desc": "少し錆びているが、中にはまだ十分な灯油が入っている。",
    },
    "iron_key": {
        "name": "鉄の鍵",
        "aliases": ["iron_key", "key", "iron"],
        "desc": "重厚な鉄製の鍵。古い錠前を開けられそうだ。",
    },
    "plank": {
        "name": "厚い木板",
        "aliases": ["plank", "board", "wood"],
        "desc": "幅広で丈夫な木の板。ちょっとした隙間なら橋代わりにできそうだ。",
    },
    "amulet": {
        "name": "蒼白い護符",
        "aliases": ["amulet", "charm", "talisman"],
        "desc": "冷たく澄んだ石が嵌め込まれた護符。不思議と胸がすっとする。",
    },
    "crystal": {
        "name": "蒼穹の結晶",
        "aliases": ["crystal", "gem", "stone"],
        "desc": "内側から青く輝く伝説の結晶。これを地上に持ち帰れば目的達成だ。",
    },
}

DIRECTIONS = {
    "n": "n", "north": "n",
    "s": "s", "south": "s",
    "e": "e", "east": "e",
    "w": "w", "west": "w",
    "u": "u", "up": "u",
    "d": "d", "down": "d",
}

DIR_JP = {
    "n": "北(n)", "s": "南(s)", "e": "東(e)",
    "w": "西(w)", "u": "上(u)", "d": "下(d)",
}

STOP_WORDS = {"the", "a", "an", "at", "to", "on", "in", "with", "into", "from"}


# ---------------------------------------------------------------------------
# ゲーム本体
# ---------------------------------------------------------------------------

class CavernGame:
    def __init__(self):
        self.loc = "entrance"
        self.inventory = []
        self.turns = 0
        self.game_over = False
        self.cleared = False

        # 光源・暗闇関連
        self.lantern_lit = False
        self.oil_level = 25
        self.max_oil = 50
        self.dark_missteps = 0

        # パズルフラグ
        self.flags = {
            "crate_opened": False,
            "rope_tied": False,
            "gear_placed": False,
            "water_drained": False,
            "plank_placed": False,
            "gate_unlocked": False,
            "vault_opened": False,
        }
        self.rune_sequence = []

        # 部屋データ
        self.rooms = {
            "entrance": {
                "name": "洞窟の入口",
                "dark": False,
                "desc": (
                    "切り立った岩壁にぽっかりと口を開けた洞窟の入口だ。\n"
                    "背後（南）には霧に煙る森へ続く帰り道が見える。\n"
                    "北の奥からは冷たく湿った風が吹き出している。"
                ),
                "exits": {"n": "moss_hall"},
                "items": [],
            },
            "moss_hall": {
                "name": "苔むした広間",
                "dark": False,
                "desc": (
                    "入口から差し込む淡い光が、壁一面を覆う緑の苔を照らしている。\n"
                    "西には崩れかけた作業場、東からは水音が聞こえる。\n"
                    "北の通路の先には重々しい鉄格子の気配がある。"
                ),
                "exits": {"s": "entrance", "w": "storage", "e": "shore", "n": "gate"},
                "items": [],
            },
            "storage": {
                "name": "崩落した資材置き場",
                "dark": False,
                "desc": (
                    "かつての採掘作業員たちが使っていた物置のようだ。\n"
                    "朽ちた棚や壊れたツルハシが散乱している。"
                ),
                "exits": {"e": "moss_hall"},
                "items": ["lantern", "crowbar", "note"],
            },
            "shore": {
                "name": "地下水脈の岸辺",
                "dark": False,
                "desc": (
                    "天井の裂け目からわずかに光が落ち、黒い水面を鈍く反射させている。\n"
                    "北には真っ暗なトンネルが続いている。"
                ),
                "exits": {"w": "moss_hall", "n": "dark_tunnel"},
                "items": ["matches"],
            },
            "island": {
                "name": "中州の石室",
                "dark": False,
                "desc": (
                    "地下水に囲まれた小さな岩島の上に、古びた石の祠が建っている。\n"
                    "静謐な空気が漂い、どこか守られているような気配がある。"
                ),
                "exits": {"w": "shore"},
                "items": ["amulet", "oil2"],
            },
            "dark_tunnel": {
                "name": "暗いトンネル",
                "dark": True,
                "desc": (
                    "素掘りの狭いトンネル。足元には深い縦穴 [chasm] が口を開けており、\n"
                    "底の方は暗くて見通せない。そばに頑丈な岩の突起がある。\n"
                    "通路は南北へ続いている。"
                ),
                "exits": {"s": "shore", "n": "junction"},
                "items": [],
            },
            "junction": {
                "name": "地底の分岐点",
                "dark": True,
                "desc": (
                    "三つの通路が交差する円形の空間だ。\n"
                    "西の壁には古い彫刻が施され、東からは油と鉄の匂いが漂っている。"
                ),
                "exits": {"s": "dark_tunnel", "w": "library", "e": "pump_room"},
                "items": [],
            },
            "library": {
                "name": "古代の書庫",
                "dark": True,
                "desc": (
                    "石造りの書架が並ぶひっそりとした部屋。書物の大半は風化しているが、\n"
                    "部屋の中央に一枚の石碑 [tablet] がきれいな状態で残っている。"
                ),
                "exits": {"e": "junction"},
                "items": ["gear", "oil1"],
            },
            "pump_room": {
                "name": "古いポンプ室",
                "dark": True,
                "desc": (
                    "巨大な排水ポンプ [pump] と錆びたレバー [lever] が据え付けられている。\n"
                    "太い鉄管が床下へと伸びている。"
                ),
                "exits": {"w": "junction"},
                "items": [],
            },
            "pit": {
                "name": "縦穴の底",
                "dark": True,
                "desc": (
                    "ひんやりとした岩盤に囲まれた縦穴の底だ。\n"
                    "頭上には垂らしたロープが伸びている。"
                ),
                "exits": {"u": "dark_tunnel"},
                "items": [],
            },
            "sunken_room": {
                "name": "沈んだ小部屋",
                "dark": True,
                "desc": (
                    "つい先ほどまで水に浸かっていたらしく、床一面に濡れた泥が溜まっている。\n"
                    "かつての探索者の遺留品がいくつか残されているようだ。"
                ),
                "exits": {"e": "pit"},
                "items": ["iron_key", "plank"],
            },
            "gate": {
                "name": "鉄格子の前",
                "dark": False,
                "desc": (
                    "通路を完全に塞ぐように、太い鉄格子 [gate] が張り巡らされている。\n"
                    "その向こう側からは不気味な冷気と霧が漂ってくる。"
                ),
                "exits": {"s": "moss_hall"},
                "items": [],
            },
            "mist_bridge": {
                "name": "瘴気の石橋",
                "dark": True,
                "desc": (
                    "底知れぬ谷底に架かる細い石橋だ。\n"
                    "濃密で息苦しい紫色の瘴気が、橋の上を這うように流れている。"
                ),
                "exits": {"s": "gate", "n": "sanctum"},
                "items": [],
            },
            "sanctum": {
                "name": "封印の広間",
                "dark": True,
                "desc": (
                    "荘厳な円蓋を持つ広間。北の壁には巨大な石扉 [door] があり、\n"
                    "その脇に三つの石のボタン――太陽 [sun]、月 [moon]、星 [star] ――が並んでいる。"
                ),
                "exits": {"s": "mist_bridge"},
                "items": [],
            },
            "vault": {
                "name": "蒼穹の祭壇",
                "dark": False,
                "desc": (
                    "洞窟の最奥に位置する静かな祭壇。\n"
                    "壁面の鉱石が淡い光を放ち、幻想的な空間を作り出している。"
                ),
                "exits": {"s": "sanctum"},
                "items": [],
            },
        }
        self.rooms["vault"]["items"].append("crystal")

    # -----------------------------------------------------------------------
    # 状態判定ヘルパー
    # -----------------------------------------------------------------------

    def has_light(self):
        room = self.rooms[self.loc]
        if not room["dark"]:
            return True
        if self.lantern_lit and ("lantern" in self.inventory or "lantern" in room["items"]):
            return True
        return False

    def find_item_id(self, target, pool):
        for item_id in pool:
            if target == item_id or target in ITEMS[item_id]["aliases"]:
                return item_id
        return None

    def show_room(self):
        room = self.rooms[self.loc]
        print(f"\n=== {room['name']} ===")

        if not self.has_light():
            print("真っ暗で何も見えない。足元も不安定だ。明かりが必要だ。")
            return

        print(room["desc"])

        # 部屋ごとの動的描写
        if self.loc == "shore":
            if not self.flags["crate_opened"]:
                print("岸辺の隅に、釘で打ち付けられた頑丈な木箱 [crate] が転がっている。")
            else:
                print("こじ開けられた木箱 [crate] が転がっている。")
            if not self.flags["plank_placed"]:
                print("東の対岸に小さな中州が見えるが、壊れた桟橋 [pier] のせいで渡れない。")
            else:
                print("壊れた桟橋に厚い木板が渡され、東の中州へ歩いて行ける。")

        elif self.loc == "dark_tunnel":
            if self.flags["rope_tied"]:
                print("岩の突起にロープがしっかり結ばれ、下(d)へ降りられるようになっている。")

        elif self.loc == "pump_room":
            if not self.flags["gear_placed"]:
                print("ポンプの側面を見ると、歯車が一枚欠けているようだ。")
            elif not self.flags["water_drained"]:
                print("真鍮の歯車がぴったり噛み合っている。あとはレバーを引くだけだ。")
            else:
                print("排水ポンプは低い駆動音を立てて順調に稼働している。")

        elif self.loc == "pit":
            if not self.flags["water_drained"]:
                print("西側に小さな横穴が見えるが、冷たい地下水が天井近くまで満ちていて進めない。")
            else:
                print("水が引き、西側(w)の小さな横穴へ入れるようになっている。")

        elif self.loc == "gate":
            if not self.flags["gate_unlocked"]:
                print("鉄格子には頑丈な錠前がかかっている。")
            else:
                print("鉄格子は大きく開け放たれ、北(n)へ進めるようになっている。")

        elif self.loc == "sanctum":
            if self.flags["vault_opened"]:
                print("北の巨大な石扉は開いており、奥から青白い光が漏れ出ている。")

        # 落ちているアイテム
        if room["items"]:
            names = [f"{ITEMS[i]['name']}[{ITEMS[i]['aliases'][0]}]" for i in room["items"]]
            print("落ちているもの: " + "、".join(names))

        # 出口一覧
        exits = [DIR_JP[d] for d in room["exits"]]
        if self.loc == "entrance":
            exits.append("外へ脱出(out)")
        print("出口: " + ", ".join(exits))

    # -----------------------------------------------------------------------
    # コマンド処理
    # -----------------------------------------------------------------------

    def consume_oil(self):
        if self.lantern_lit:
            self.oil_level -= 1
            if self.oil_level == 5:
                print("（※ランタンの炎が弱まってきた。オイル残量があとわずかだ！）")
            elif self.oil_level <= 0:
                self.oil_level = 0
                self.lantern_lit = False
                print("（※ジュッという音とともにランタンの火が消えた！オイル切れだ！）")

    def cmd_move(self, direction):
        if not self.has_light():
            self.dark_missteps += 1
            if self.dark_missteps >= 2:
                print("\n暗闇の中で足を踏み外し、深い亀裂へと滑落してしまった……。")
                print("意識が遠のいていく。")
                self.game_over = True
                return
            print("真っ暗でどこへ進んでいるのか分からない！これ以上むやみに動くと危険だ。")
            return

        # 特殊移動チェック
        if self.loc == "mist_bridge" and direction == "n" and "amulet" not in self.inventory:
            print("強烈な瘴気が肺を焼き、とても前へ進めない。何か身を守るものが必要だ。")
            return

        room = self.rooms[self.loc]
        if direction not in room["exits"]:
            if self.loc == "entrance" and direction == "s":
                self.cmd_leave()
                return
            print("その方向へは進めない。")
            return

        self.loc = room["exits"][direction]
        self.dark_missteps = 0
        self.turns += 1
        self.consume_oil()
        self.show_room()

    def cmd_leave(self):
        if self.loc != "entrance":
            print("ここからは外に出られない。入口まで戻る必要がある。")
            return
        if "crystal" in self.inventory:
            print("\nあなたは『蒼穹の結晶』を胸に抱き、ついに洞窟の外へと生還した！")
            print("森の木漏れ日が、手の中の青い結晶を眩しく照らし出している。")
            self.cleared = True
            self.game_over = True
        else:
            print("まだ『蒼穹の結晶』を見つけていない。手ぶらで帰るわけにはいかない。")

    def cmd_get(self, target):
        if not self.has_light():
            print("暗すぎて手探りでは見つけられない。")
            return
        if not target:
            print("何を取る？（例: get lantern）")
            return
        room = self.rooms[self.loc]
        item_id = self.find_item_id(target, room["items"])
        if not item_id:
            print("ここにはそのようなものは見当たらない。")
            return
        room["items"].remove(item_id)
        self.inventory.append(item_id)
        print(f"{ITEMS[item_id]['name']} を手に入れた。")

    def cmd_drop(self, target):
        if not target:
            print("何を置く？（例: drop note）")
            return
        item_id = self.find_item_id(target, self.inventory)
        if not item_id:
            print("それは持っていない。")
            return
        self.inventory.remove(item_id)
        self.rooms[self.loc]["items"].append(item_id)
        print(f"{ITEMS[item_id]['name']} をその場に置いた。")

    def cmd_inventory(self):
        if not self.inventory:
            print("持ち物は何もない。")
            return
        print("【持ち物】")
        for item_id in self.inventory:
            extra = ""
            if item_id == "lantern":
                state = "点灯中" if self.lantern_lit else "消灯"
                extra = f" ({state} / オイル残量: {self.oil_level})"
            print(f" - {ITEMS[item_id]['name']} [{ITEMS[item_id]['aliases'][0]}]{extra}")

    def cmd_examine(self, target):
        if not self.has_light():
            print("暗くてよく見えない。")
            return
        if not target:
            self.show_room()
            return

        # 所持品または部屋のアイテム
        item_id = self.find_item_id(target, self.inventory + self.rooms[self.loc]["items"])
        if item_id:
            print(ITEMS[item_id]["desc"])
            if item_id == "lantern":
                state = "点灯している" if self.lantern_lit else "消えている"
                print(f"現在は{state}。オイル残量は {self.oil_level}/{self.max_oil} だ。")
            return

        # 部屋固有のオブジェクト
        if self.loc == "shore" and target in ("crate", "box"):
            if not self.flags["crate_opened"]:
                print("太い釘でしっかり閉じられた木箱だ。素手では開けられそうにない。")
            else:
                print("バールでこじ開けられた空の木箱だ。")
        elif self.loc == "shore" and target in ("pier", "bridge", "water"):
            if not self.flags["plank_placed"]:
                print("桟橋の途中が崩落して2メートルほどの隙間が空いている。丈夫な板があれば渡れそうだ。")
            else:
                print("厚い木板がしっかり架けられている。")
        elif self.loc == "dark_tunnel" and target in ("chasm", "hole", "pit"):
            print("真っ暗な縦穴が下へと伸びている。ロープがあれば降りられそうだ。")
        elif self.loc == "library" and target in ("tablet", "stone"):
            self.cmd_read("tablet")
        elif self.loc == "pump_room" and target in ("pump", "machine"):
            if not self.flags["gear_placed"]:
                print("排水ポンプの駆動部から、歯車が一つ抜け落ちている。")
            else:
                print("歯車は正しく収まっている。")
        elif self.loc == "pump_room" and target == "lever":
            print("ポンプを起動させるための重い鉄製レバーだ。")
        elif self.loc == "gate" and target in ("gate", "lock", "door"):
            if not self.flags["gate_unlocked"]:
                print("錆びついた頑丈な鉄格子。鉄の鍵穴がついている。")
            else:
                print("解錠された鉄格子が開いている。")
        elif self.loc == "sanctum" and target in ("door", "buttons", "sun", "moon", "star"):
            print("石扉の脇に太陽[sun]・月[moon]・星[star]のボタンがある。正しい順で押す仕掛けのようだ。")
        else:
            print("特に変わったところは見つからない。")

    def cmd_read(self, target):
        if not self.has_light():
            print("暗くて文字が読めない。")
            return
        if target in ("note", "memo", "paper") and (
            "note" in self.inventory or "note" in self.rooms[self.loc]["items"]
        ):
            print(
                "--- 作業員のメモ ---\n"
                "『奥のトンネルは完全な暗闇だ。ランタンなしでは一歩も進むな。\n"
                " 明るい場所では火を消して(off lantern)オイルを節約すること。\n"
                " 鉄格子の先の石橋には毒の瘴気が満ちている。\n"
                " 中州の祠にある護符がなければ、とても渡りきれまい……』"
            )
        elif self.loc == "library" and target in ("tablet", "stone", "stele"):
            print(
                "--- 古代の石碑 ---\n"
                "『蒼穹の宝を求める者よ、天の理を順に示せ。\n"
                " まず「星(star)」が永き闇を貫き、\n"
                " 次に「月(moon)」が深き潮を導き、\n"
                " 最後に「太陽(sun)」が封印の扉を開く。』"
            )
        else:
            print("それは読めない。")

    def cmd_light(self, target):
        if target not in ("lantern", "lamp", ""):
            print("それに火を点けることはできない。")
            return
        if "lantern" not in self.inventory:
            print("ランタンを持っていない。")
            return
        if self.lantern_lit:
            print("ランタンはすでに点いている。")
            return
        if "matches" not in self.inventory:
            print("火を点けるためのマッチを持っていない。")
            return
        if self.oil_level <= 0:
            print("オイルが空で火が点かない！予備のオイル缶が必要だ。")
            return
        self.lantern_lit = True
        self.dark_missteps = 0
        print("マッチを擦り、ランタンに火を灯した。暖かな光が周囲を照らし出す。")
        if self.rooms[self.loc]["dark"]:
            self.show_room()

    def cmd_extinguish(self, target):
        if target not in ("lantern", "lamp", ""):
            print("それは消せない。")
            return
        if not self.lantern_lit:
            print("ランタンはすでに消えている。")
            return
        self.lantern_lit = False
        print("ランタンの火を消した。")

    def cmd_open(self, target):
        if not self.has_light():
            print("暗くて手元が見えない。")
            return
        if self.loc == "shore" and target in ("crate", "box"):
            if self.flags["crate_opened"]:
                print("木箱はすでに開いている。")
                return
            if "crowbar" not in self.inventory:
                print("釘で固く閉じられている。バールのような道具が必要だ。")
                return
            self.flags["crate_opened"] = True
            self.rooms["shore"]["items"].append("rope")
            print("鉄のバールを隙間に差し込み、力任せに木箱をこじ開けた！")
            print("中から 丈夫なロープ[rope] が現れた。")
        elif self.loc == "gate" and target in ("gate", "lock", "door"):
            if self.flags["gate_unlocked"]:
                print("鉄格子はすでに開いている。")
                return
            if "iron_key" not in self.inventory:
                print("鍵がかかっている。鉄の鍵が必要だ。")
                return
            self.flags["gate_unlocked"] = True
            self.rooms["gate"]["exits"]["n"] = "mist_bridge"
            print("鉄の鍵を差し込んで回すと、重い音を立てて鉄格子が開いた！")
        else:
            print("それは開けられない。")

    def cmd_tie(self, target):
        if not self.has_light():
            print("暗くて作業できない。")
            return
        if self.loc != "dark_tunnel":
            print("ここでロープを結ぶ必要はなさそうだ。")
            return
        if self.flags["rope_tied"]:
            print("ロープはすでにしっかり結んである。")
            return
        if "rope" not in self.inventory:
            print("ロープを持っていない。")
            return
        self.inventory.remove("rope")
        self.flags["rope_tied"] = True
        self.rooms["dark_tunnel"]["exits"]["d"] = "pit"
        print("頑丈な岩の突起にロープを結び、縦穴の下(d)へと垂らした！")

    def cmd_pull(self, target):
        if not self.has_light():
            print("暗くてレバーの位置が分からない。")
            return
        if self.loc != "pump_room" or target not in ("lever", "pump"):
            print("引けそうなものはない。")
            return
        if self.flags["water_drained"]:
            print("ポンプはすでに稼働している。")
            return
        if not self.flags["gear_placed"]:
            print("レバーを引いたが、空回りして動かない。歯車が欠けているせいだ。")
            return
        self.flags["water_drained"] = True
        self.rooms["pit"]["exits"]["w"] = "sunken_room"
        print("レバーを力いっぱい引き下げた！")
        print("ゴゴゴ……と轟音が響き渡り、地底のどこかから大量の水が抜けていく音がした！")

    def cmd_push(self, target):
        if not self.has_light():
            print("暗くてボタンが見えない。")
            return
        if self.loc != "sanctum":
            print("押せそうなものは見当たらない。")
            return
        if self.flags["vault_opened"]:
            print("石扉はすでに開いている。")
            return
        if target not in ("sun", "moon", "star"):
            print("押せるボタンは sun, moon, star の三つだ。")
            return

        self.rune_sequence.append(target)
        jp_map = {"sun": "太陽", "moon": "月", "star": "星"}
        print(f"『{jp_map[target]}』のボタンを押し込んだ。カチリと低い音が鳴る。")

        if len(self.rune_sequence) == 3:
            if self.rune_sequence == ["star", "moon", "sun"]:
                self.flags["vault_opened"] = True
                self.rooms["sanctum"]["exits"]["n"] = "vault"
                print("ズズズ……と地響きが起き、北の巨大な石扉がゆっくりと開かれた！")
            else:
                self.rune_sequence = []
                print("ガチャン！と乾いた音が鳴り、三つのボタンが元の位置に飛び出した。")
                print("どうやら押す順番が間違っていたようだ。")

    def cmd_use(self, target):
        if not target:
            print("何を使う？（例: use key）")
            return
        item_id = self.find_item_id(target, self.inventory)
        if not item_id:
            print("それは持っていない。")
            return

        if item_id in ("oil1", "oil2"):
            if "lantern" not in self.inventory:
                print("オイルを注ぐランタンを持っていない。")
                return
            self.inventory.remove(item_id)
            self.oil_level = min(self.max_oil, self.oil_level + 25)
            print(f"ランタンにオイルを補給した。（現在のオイル残量: {self.oil_level}/{self.max_oil}）")
        elif item_id in ("matches", "lantern"):
            self.cmd_light("lantern")
        elif item_id == "crowbar":
            self.cmd_open("crate")
        elif item_id == "rope":
            self.cmd_tie("rope")
        elif item_id == "iron_key":
            self.cmd_open("gate")
        elif item_id == "gear":
            if self.loc != "pump_room":
                print("ここでは使い道がなさそうだ。")
                return
            if not self.has_light():
                print("暗くて取り付けられない。")
                return
            self.inventory.remove("gear")
            self.flags["gear_placed"] = True
            print("ポンプの欠けた部分に真鍮の歯車をはめ込んだ。ぴったりと噛み合った！")
        elif item_id == "plank":
            if self.loc != "shore":
                print("ここで板を敷く必要はなさそうだ。")
                return
            self.inventory.remove("plank")
            self.flags["plank_placed"] = True
            self.rooms["shore"]["exits"]["e"] = "island"
            print("壊れた桟橋の隙間に厚い木板を架けた。これで東(e)の中州へ渡れる！")
        elif item_id == "note":
            self.cmd_read("note")
        elif item_id == "amulet":
            print("護符は持っているだけで不思議な力を発揮するようだ。")
        else:
            print("ここではどう使えばいいか分からない。")

    def cmd_help(self):
        print(
            "\n--- コマンド一覧（英語入力） ---\n"
            "  n / s / e / w / u / d  : 北・南・東・西・上・下へ移動\n"
            "  out / leave            : 洞窟の入口から外へ脱出\n"
            "  look (l)               : 周囲を見渡す\n"
            "  examine (x) <対象>     : アイテムや仕掛けを詳しく調べる\n"
            "  get <対象>             : アイテムを拾う\n"
            "  drop <対象>            : アイテムを置く\n"
            "  use <対象>             : アイテムを使う\n"
            "  open <対象>            : 箱や扉を開ける\n"
            "  read <対象>            : メモや石碑を読む\n"
            "  light / off lantern    : ランタンを点灯 / 消灯する\n"
            "  tie rope               : ロープを結ぶ\n"
            "  pull <対象>            : レバーなどを引く\n"
            "  push <対象>            : ボタンなどを押す\n"
            "  inv (i)                : 持ち物とオイル残量を確認\n"
            "  help (h) / quit (q)    : ヘルプ表示 / ゲーム終了"
        )

    # -----------------------------------------------------------------------
    # パーサーとメインループ
    # -----------------------------------------------------------------------

    def parse_and_execute(self, raw_input):
        words = [w for w in raw_input.strip().lower().split() if w not in STOP_WORDS]
        if not words:
            return

        verb = words[0]
        target = words[1] if len(words) > 1 else ""

        if verb in DIRECTIONS:
            self.cmd_move(DIRECTIONS[verb])
        elif verb == "go" and target in DIRECTIONS:
            self.cmd_move(DIRECTIONS[target])
        elif verb in ("out", "leave", "escape"):
            self.cmd_leave()
        elif verb in ("l", "look"):
            if target:
                self.cmd_examine(target)
            else:
                self.show_room()
        elif verb in ("x", "examine", "check", "inspect"):
            self.cmd_examine(target)
        elif verb in ("get", "take", "pick"):
            self.cmd_get(target)
        elif verb in ("drop", "put"):
            if target == "gear" and self.loc == "pump_room":
                self.cmd_use("gear")
            else:
                self.cmd_drop(target)
        elif verb in ("i", "inv", "inventory"):
            self.cmd_inventory()
        elif verb in ("use", "apply"):
            self.cmd_use(target)
        elif verb in ("open", "unlock", "pry"):
            self.cmd_open(target)
        elif verb == "read":
            self.cmd_read(target)
        elif verb in ("light", "on"):
            self.cmd_light(target)
        elif verb in ("extinguish", "off"):
            self.cmd_extinguish(target)
        elif verb == "tie":
            self.cmd_tie(target)
        elif verb == "pull":
            self.cmd_pull(target)
        elif verb in ("push", "press"):
            self.cmd_push(target)
        elif verb in ("h", "help", "?"):
            self.cmd_help()
        elif verb in ("q", "quit", "exit"):
            print("探検を中断しました。")
            self.game_over = True
        else:
            print("そのコマンドは理解できない。（'help' でコマンド一覧を表示）")

    def run(self):
        print("==================================================")
        print("      THE DEEP CAVERN  〜忘れられた鉱脈の奥底〜")
        print("==================================================")
        print("目的: 洞窟の最奥に眠る『蒼穹の結晶』を手に入れ、")
        print("      洞窟の入口から地上へ生還すること。")
        print("（※操作は英語コマンドで行います。'help' で一覧表示）")

        self.show_room()

        while not self.game_over:
            try:
                cmd = input("\n> ")
            except (EOFError, KeyboardInterrupt):
                print("\n探検を終了します。")
                break
            self.parse_and_execute(cmd)

        if self.cleared:
            print("\n==================================================")
            print(f"  GAME CLEAR!  総移動ターン数: {self.turns}")
            if self.turns <= 28:
                rank = "S（伝説の探検家）"
            elif self.turns <= 40:
                rank = "A（熟練の冒険者）"
            else:
                rank = "B（生還者）"
            print(f"  評価ランク: {rank}")
            print("==================================================")


if __name__ == "__main__":
    CavernGame().run()