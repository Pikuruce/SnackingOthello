from lib.src.components.object import Object
from lib.src.components.character import Character
from typing import Callable
from direct.task import Task
from lib.src.composables.object_scenario import movePosition, moveRotation
from panda3d.core import ClockObject

class OthelloBoard:
    def __init__(self, base) -> None:
        self.base = base
        self.turn = "B"
        self.winner = None

        self.is_flipping = False
        self.is_eating = False

        self.save_data = []

        self.max_eat = 64
        self.b_eat = 0
        self.w_eat = 0
        self.eat_interval = 0.2
        self.eat_timer = 0.0

        self.clock = ClockObject.get_global_clock()

        self.board_obj = Object(self.base, "SnackingOthello_Board")
        self.board_obj.setPos(-16, -32, 14)
        
        # 3Dクッキーオブジェクトを [行][列] で管理するための辞書
        # キー: (row, col) -> 値: クッキーのObjectインスタンス
        self.cookie_objects: dict[tuple[int, int], Object] = {}

        # 64ビット整数2つで管理
        self.bb_black: int = 0
        self.bb_white: int = 0
        
        self.initializeBoard()

        self.arrow = Character(self.base, "SnackingOthello_Arrow", is_two_sided=True)
        self.arrow.setScale(4, 4, 4)
        self.arrow.setSelfFunction(moveRotation([(36000, 0, 0)], loop=True, speed=90))
        self.arrow.setOnTrigger(True)
        self.arrow.setContinuous(True)
        self.arrow.reparent(self.board_obj.node)
        self.setArrowPos(0, 0)
        self.setArrowColor()

    def initializeBoard(self) -> None:
        """
        初期配置（中央の4手）をビットボードと3D画面にセット
        """

        # ビットボードの初期化
        self.bb_white = (1 << 27) | (1 << 36)
        self.bb_black = (1 << 28) | (1 << 35)

        # 3D画面上の初期クッキー配置
        # 白: (3,3), (4,4) / 黒: (3,4), (4,3)
        self.placeCookie(3, 3, "W")
        self.placeCookie(3, 4, "B")
        self.placeCookie(4, 3, "B")
        self.placeCookie(4, 4, "W")

    def canAct(self) -> bool:
        """
        次の手を打ってもよいかどうか判断
        """
        return not (self.is_flipping or self.is_eating or self.winner)

    def actByEnter(self, row, col) -> str:
        """
        次の手を打つ
        """
        if not self.canAct():
            return "no"

        if self.eatPiece(row, col):
            self.base.playEat()
            self.winnerCheck()
            self.save_data.append([row, col])
            return "eat"

        if self.placePiece(row, col):
            self.base.playCookieSelect()
            self.save_data.append([row, col])
            return "place"

        return "no"

    def restartCheck(self) -> bool:
        """
        両者が手詰まりか判定し、手詰まりだった場合盤面をリセットする
        """
        b_val = self.getMovablePositionsWithCounts("B")
        w_val = self.getMovablePositionsWithCounts("W")
        if len(b_val) + len(w_val) == 0:
            # 盤面に残っているクッキーをすべて食べる
            self.base.taskMgr.add(self.eatAllCookie, "eat_all_cookie")
            return True
        return False

    def winnerCheck(self) -> None:
        """
        決着がついているかどうか
        """
        if self.b_eat >= self.max_eat:
            self.winner = "B"
        elif self.w_eat >= self.max_eat:
            self.winner = "W"

    def eatPiece(self, row, col) -> bool:
        """
        指定されたマスのクッキーを食べる
        """

        target_bit = 1 << (row * 8 + col)

        if self.turn == "B":
            player, opponent = self.bb_black, self.bb_white
        else:
            player, opponent = self.bb_white, self.bb_black

        player &= ~target_bit
        flag = False
        if self.turn == "B":
            if player != self.bb_black:
                self.b_eat += 1
                self.bb_black = player
                flag = True
        else:
            if player != self.bb_white:
                self.w_eat += 1
                self.bb_white = player
                flag = True

        if flag:
            target_obj = self.cookie_objects.pop((row, col), None)
            target_obj.remove()
            if self.turn == "B":
                self.bb_black, self.bb_white = player, opponent
                self.turn = "W"
            else:
                self.bb_white, self.bb_black = player, opponent
                self.turn = "B"
            self.setArrowColor()
            return True

        return False
        

    def placePiece(self, row, col) -> bool:
        """
        指定されたマスに石を置く（ビット計算 ＋ 3Dアニメーション連動）
        """
        
        target_bit = 1 << (row * 8 + col)
        
        if not self.isValidMove(row, col):
            return False

        if self.turn == "B":
            player, opponent = self.bb_black, self.bb_white
        else:
            player, opponent = self.bb_white, self.bb_black

        # ひっくり返る敵の石の「ビットパターン」を取得
        flipped_mask = self._getFlippedMask(target_bit, player, opponent)

        for r in range(8):
            for c in range(8):
                shift = r * 8 + c
                # ひっくり返るマスクのビットが立っている場所を探す
                if flipped_mask & (1 << shift):
                    # 記憶しておいた3Dオブジェクトを辞書から引っ張り出す
                    target_cookie = self.cookie_objects.get((r, c))
                    if target_cookie:
                        # 3D画面上のクッキーをひっくり返す
                        target_cookie.setOnTrigger(True)

        self.is_flipping = True

        # 新しく置いたマスのクッキーを3D画面上に生成
        self.placeCookie(row, col, self.turn)

        # ビットボード盤面の更新
        player |= target_bit
        player |= flipped_mask
        opponent &= ~flipped_mask

        if self.turn == "B":
            self.bb_black, self.bb_white = player, opponent
            self.turn = "W"
        else:
            self.bb_white, self.bb_black = player, opponent
            self.turn = "B"

        self.setArrowColor()
            
        return True

    def _getFlippedMask(self, target_bit: int, player: int, opponent: int) -> int:
        """
        指定されたマスに置いたとき、ひっくり返る敵の石のビットパターンを返す内部関数
        """
        mask_l = 0x7F7F7F7F7F7F7F7F
        mask_r = 0xFEFEFEFEFEFEFEFE
        mask_a = 0xFFFFFFFFFFFFFFFF

        directions = [
            {"shift": 1,  "mask": mask_l, "type": "right"}, # 右
            {"shift": 7,  "mask": mask_r, "type": "right"}, # 左下
            {"shift": 8,  "mask": mask_a, "type": "right"}, # 下
            {"shift": 9,  "mask": mask_l, "type": "right"}, # 右下
            {"shift": 1,  "mask": mask_r, "type": "left"},  # 左
            {"shift": 7,  "mask": mask_l, "type": "left"},  # 右上
            {"shift": 8,  "mask": mask_a, "type": "left"},  # 上
            {"shift": 9,  "mask": mask_r, "type": "left"},  # 左上
        ]

        flipped_mask = 0
        for d in directions:
            s = d["shift"]
            m = d["mask"]
            
            if d["type"] == "right":
                t = (target_bit >> s) & opponent & m

                for _ in range(5):
                    t |= (t >> s) & opponent & m

                if ((t >> s) & m) & player:
                    flipped_mask |= t

            else:
                t = (target_bit << s) & opponent & m

                for _ in range(5):
                    t |= (t << s) & opponent & m

                if ((t << s) & m) & player:
                    flipped_mask |= t
                    
        return flipped_mask

    def getMovablePositionsWithCounts(self, color: str) -> list[tuple[int, int, int]]:
        """
        設置可能なすべてのマスと、ひっくり返せる石の数を計算
        """
        player = self.bb_black if color == "B" else self.bb_white
        opponent = self.bb_white if color == "B" else self.bb_black
        blank = ~(player | opponent) & 0xFFFFFFFFFFFFFFFF

        movable_list = []

        # 空きマスのビットだけをループで回す（高速化のため）
        temp_blank = blank
        while temp_blank > 0:
            # 最下位ビット（一番右にある1）を1つだけ取り出すテクニック
            target_bit = temp_blank & -temp_blank
            
            # target_bit が全体の何番目のビットか（0〜63）を逆算して行と列を特定
            pos_shift = target_bit.bit_length() - 1
            r, c = divmod(pos_shift, 8)

            # ひっくり返せる数を計算
            flipped_mask = self._getFlippedMask(target_bit, player, opponent)
            total_flipped = bin(flipped_mask).count("1")

            if total_flipped > 0:
                movable_list.append((r, c, total_flipped))

            # 処理し終わったビットを消して次のループへ
            temp_blank ^= target_bit

        return movable_list

    def isValidMove(self, row, col) -> bool:
        """
        設置可能かどうかを調べる
        """
        valid_moves = self.getMovablePositionsWithCounts(color=self.turn)
        return any(r == row and c == col for r, c, _ in valid_moves)

    def placeCookie(self, row: int, col: int, color: str) -> None:
        """
        指定されたマスにクッキーを生成し、辞書で管理する（初期化・着手共通）
        """
        cookie = Object(self.base, "SnackingOthello_Cookie")
        cookie.reparent(self.board_obj.node)  # 親ノードを盤面に設定
        cookie.setAnchor(0, 0, 1)
        cookie.setScale(0.25)
        cookie.setPos(col * 2 - 7, row * 2 - 7, 1.25, init_pos=True)
        
        if color == "B":
            cookie.setRotate(0, 0, 180)      # 黒のクッキー
        else:
            cookie.setRotate(0, 0, 0)    # 白のクッキー

        cookie.setSelfFunction(self.cookieFlipFunction())  # クッキーをひっくり返す関数をセット
            
        self.cookie_objects[(row, col)] = cookie

    def setArrowPos(self, row: int, col: int) -> None:
        """
        矢印の位置を設定
        """
        self.arrow.setPos(col * 2 - 7, row * 2 - 7, 1)

    def setArrowColor(self) -> None:
        """
        矢印の色を設定
        """
        self.arrow.animator.play("front", "buliot" if self.turn == "B" else "silky")

    def cookieFlipFunction(self) -> Callable[[Object, float], None]:
        """
        クッキーをひっくり返す関数を返す
        """
        pos_func = movePosition([(0, 0, 1)], speed=8)
        rot_func = moveRotation([(0, 0, 180)], speed=540)
        def flip(target: Object, dt: float) -> None:
            restart_pos = pos_func(target, dt)
            restart_rot = rot_func(target, dt)
            if restart_pos and restart_rot:
                restart_pos()
                restart_rot()
                target.on_trigger = False

        return flip

    def getBlackRatio(self) -> int:
        """
        満腹度に対する現在の割合を返す
        """
        return int(self.b_eat // (self.max_eat / 8))

    def getWhiteRatio(self) -> int:
        """
        満腹度に対する現在の割合を返す
        """
        return int(self.w_eat // (self.max_eat / 8))

    def eatAllCookie(self, task: Task) -> Task:
        """
        すべてのクッキーを食べる
        """
        self.is_eating = True
        if self.is_flipping:
            return task.cont

        dt = self.clock.getDt()
        self.eat_timer += dt

        if self.eat_timer >= self.eat_interval:
            self.eat_timer = 0.0
            if len(self.cookie_objects.values()) == 0:
                self.is_eating = False
                self.initializeBoard()
                return task.done
            (key, value) = self.cookie_objects.popitem()
            row, col = key

            bit = 1 << (row * 8 + col)

            if self.bb_black & bit:
                self.b_eat += 1
            elif self.bb_white & bit:
                self.w_eat += 1

            value.remove()
            self.base.playEat()
            self.winnerCheck()

        return task.cont

    def resetGame(self) -> None:
        """
        内容をすべてリセット
        """
        self.w_eat = 0
        self.b_eat = 0
        self.winner = None
        while self.cookie_objects:
            _, cookie = self.cookie_objects.popitem()
            cookie.remove()
        self.initializeBoard()

    def destroy(self) -> None:
        """
        終了用
        """
        self.base.taskMgr.remove("eat_all_cookie")
        self.w_eat = 0
        self.b_eat = 0
        self.winner = None
        self.save_data.clear()
        self.board_obj.remove()
        while self.cookie_objects:
            _, cookie = self.cookie_objects.popitem()
            cookie.remove()

    def getSaveData(self) -> list[list[int]]:
        """
        記録した試合の内容を返す
        """
        return self.save_data

    def setMaxeat(self, val: int) -> None:
        """
        勝利条件の数値を設定
        """
        self.max_eat = val

    def update(self, dt: float) -> bool:
        """
        毎フレーム呼ばれる更新関数
        """
        for cookie in self.cookie_objects.values():
            cookie.update(dt)

        self.arrow.update(dt)

        if self.is_flipping and not any(cookie.on_trigger for cookie in self.cookie_objects.values()):
            self.is_flipping = False
            return True

        return False
