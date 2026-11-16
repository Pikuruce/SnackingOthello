from lib.src.composables.play_base import PlayBase
from lib.src.networks.lan_discovery import LanDiscoveryHost
from lib.src.networks.tcp_host import TcpHost
from lib.src.networks.tcp_client import TcpClient
from lib.src.components.text_input import TextInput
from lib.src.networks.room_host import generateRoomCode
from lib.src.networks.room_client import findLanRoom
from lib.src.networks.protocol import encodeMessage, decodeMessage
from lib.src.networks.net_utils import getLocalIPv4Addresses, parseIPv4
from lib.src.components.select_screen import SelectScreen
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
import threading, queue

TCP_PORT = 50000

class PlayOnline(PlayBase):
    def __init__(self, game, is_host: bool):
        super().__init__(game)

        self.is_host = is_host

        self.room = SelectScreen(self.base)
        self.room.setScreenColor(0, 0, 0, 1)
        self.room.addItem("もどる", self.endGame)
        self.room.openScreen()
        self.keyboard_controller.setPermission(False)
        self.keyboard_controller.setKeyEvent("arrow_up", "up", lambda: self.pointerMove(1, 0), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("arrow_down", "down", lambda: self.pointerMove(-1, 0), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("arrow_left", "left", lambda: self.pointerMove(0, -1), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("arrow_right", "right", lambda: self.pointerMove(0, 1), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("enter", "enter", self.enter)
        self.gameover.addItem("しゅうりょう", self.endGame)
        self.room_input = None
        self.host_data = None

        self.network = None
        self.discovery = None

        self.search_result = queue.Queue()
        self.searching = False
        self.connecting = False
        self.discovery_error_shown = False

        self.connected = False
        self.match_started = False
        self.is_my_turn = False

        # 接続状況・エラーを表示する補助テキスト
        self.status_text = OnscreenText(
            text="",
            parent=self.room.screen,
            pos=(0, -0.45),
            scale=0.05,
            wordwrap=34,
            fg=(1, 1, 1, 1),
            font=self.room.game_font,
            align=TextNode.ACenter,
            mayChange=True,
        )

        # ホスト・クライアント共通で登録
        self.base.taskMgr.add(
            self.updateNetwork,
            "updateNetwork"
        )

        if self.is_host:
            self.room_code = generateRoomCode()
            self.room.setExplain(
                f"待機中・・・\nRoom Code: {self.room_code}"
            )
            addresses = getLocalIPv4Addresses()
            if addresses:
                self.setStatus(
                    "見つからない時は相手にIPを入力してもらう\n"
                    + "\n".join(f"IP: {address}" for address in addresses)
                )
            self.network = TcpHost(port=TCP_PORT)
            self.network.start()
        else:
            self.room.setExplain("ルームコード\nまたは ホストIP")

            self.room_input = TextInput(
                self.base,
                width=12,
            )
            self.room.addItem("さんか", self.joinRoom)

    def setStatus(self, text: str) -> None:
        self.status_text.setText(text)

    def updateNetwork(self, task: Task):

        # LAN検索結果
        try:
            result = self.search_result.get_nowait()
            self.searching = False

            if isinstance(result, OSError):
                print(f"Discovery error: {result}")
                self.setStatus(f"検索に失敗しました\n{result}")

            elif result is None:
                print("Room not found")
                self.setStatus(
                    "ルームが見つかりませんでした\n"
                    "ホストのファイアウォール設定を確認するか\n"
                    "ホスト画面のIPを入力してください"
                )

            else:
                self.connectTo(result["host"], result["port"])

        except queue.Empty:
            pass

        # ホスト側のUDP探索受付が失敗していたら知らせる（IP直接入力なら接続できる）
        if (
            self.discovery is not None
            and self.discovery.error is not None
            and not self.discovery_error_shown
        ):
            self.discovery_error_shown = True
            self.setStatus(
                "ルーム検索を受け付けられません\n"
                f"{self.discovery.error}\n"
                "相手にIPを直接入力してもらってください"
            )

        # TCPイベント
        if self.network is not None:
            while True:
                try:
                    event, data = self.network.events.get_nowait()
                except queue.Empty:
                    break

                if event == "listening":
                    print(f"Waiting on port: {data}")

                    # ホストだけがUDP Discoveryを起動
                    if self.is_host and self.discovery is None:
                        self.discovery = LanDiscoveryHost(
                            self.room_code,
                            tcp_port=data
                        )
                        self.discovery.start()

                elif event == "connected":
                    print(f"Connected: {data}")
                    self.startMatch()

                elif event == "message":
                    message = decodeMessage(data)
                    self.receiveAction(message)

                elif event == "disconnected":
                    print("相手が切断しました")
                    self.endGame()
                    return Task.done

                elif event == "error":
                    print(f"Network error: {data}")
                    if not self.match_started:
                        self.connecting = False
                        if self.is_host:
                            self.setStatus(f"待ち受けを開始できませんでした\n{data}")
                        else:
                            self.setStatus(f"接続できませんでした\n{data}")

        if self.connected:
            self.updateTurnPermission()

        return task.cont

    def endGame(self) -> None:
        super().endGame()
        self.room.closeScreen()

        if self.room_input is not None:
            self.room_input.close()

        if self.discovery is not None:
            self.discovery.close()

        if self.network is not None:
            self.network.close()

    def connectTo(self, host: str, port: int) -> None:
        if self.network is not None:
            self.network.close()

        self.connecting = True
        self.host_data = {"host": host, "port": port}
        self.setStatus(f"{host} に接続中・・・")

        self.network = TcpClient(host, port)
        self.network.connect()

    def joinRoom(self):
        if self.searching or self.connecting:
            return

        text = self.room_input.getText().strip()

        # IPアドレスが入力されたら検索せず直接接続
        ip = parseIPv4(text)
        if ip is not None:
            self.connectTo(ip, TCP_PORT)
            return

        room_code = text.upper()

        if len(room_code) != 6:
            self.setStatus("6文字のルームコードか\nIPアドレスを入力してください")
            return

        self.setStatus("ルームを探しています・・・")
        self.searching = True

        threading.Thread(
            target=self.searchRoom,
            args=(room_code,),
            daemon=True
        ).start()


    def searchRoom(self, room_code: str):
        try:
            result = findLanRoom(room_code)
            self.search_result.put(result)
        except OSError as e:
            self.search_result.put(e)

    def startMatch(self):
        if self.match_started:
            return

        self.match_started = True
        self.connected = True
        if self.is_host:
            self.is_my_turn = True

        self.room.closeScreen()

        if self.room_input is not None:
            self.room_input.close()
            self.room_input = None

        self.updateTurnPermission()

    def updateTurnPermission(self):
        if not self.connected or self.is_clear:
            self.is_my_turn = False
            self.keyboard_controller.setPermission(False)
            return

        self.is_my_turn = (
            (self.is_host and self.othello_board.turn == "B")
            or
            (not self.is_host and self.othello_board.turn == "W")
        )

        self.keyboard_controller.setPermission(self.is_my_turn)

    def enter(self) -> None:
        if self.is_my_turn:
            if self.menu.keyboard_controller.permission:
                return
            result = self.othello_board.actByEnter(self.select_pointer[0], self.select_pointer[1])
            if result == "place":
                if self.othello_board.turn == "B":
                    self.silky.playAnimation("front", "act", loop=False)
                else:
                    self.buliot.playAnimation("front", "act", loop=False)
            elif result == "eat":
                if self.othello_board.turn == "B":
                    self.silky.playAnimation("front", "eat")
                else:
                    self.buliot.playAnimation("front", "eat")
    
            if result == "place" or result == "eat":
                self.sendAction(
                    "enter",
                    self.select_pointer[0],
                    self.select_pointer[1]
                )
                if self.othello_board.restartCheck():
                    self.silky.playAnimation("front", "eat")
                    self.buliot.playAnimation("front", "eat")
    
            self.updateStomach()

    def sendAction(self, action: str, row: int, col: int):
        if self.network is None:
            return

        # protocol.py のエンコード関数を利用
        data = encodeMessage(action, row, col)
        self.network.send(data)

    def pointerMove(self, dx: int, dy: int):
        if not self.is_my_turn:
            return

        super().pointerMove(dx, dy)

        self.sendAction(
            "move",
            self.select_pointer[0],
            self.select_pointer[1]
        )

    def receiveAction(self, message: dict):
        action = message["action"]
        row, col = message["position"]

        if action == "move":
            self.select_pointer = [row, col]
            self.othello_board.setArrowPos(row, col)
            self.base.playCookieSelect()

        elif action == "enter":
            self.select_pointer = [row, col]
            self.othello_board.setArrowPos(row, col)
            result = self.othello_board.actByEnter(row, col)

            if result == "place":
                if self.othello_board.turn == "W":
                    self.buliot.playAnimation("front", "act", loop=False)
                else:
                    self.silky.playAnimation("front", "act", loop=False)

            elif result == "eat":
                if self.othello_board.turn == "W":
                    self.buliot.playAnimation("front", "eat")
                else:
                    self.silky.playAnimation("front", "eat")

            if result == "place" or result == "eat":
                if self.othello_board.restartCheck():
                    self.silky.playAnimation("front", "eat")
                    self.buliot.playAnimation("front", "eat")

            self.updateStomach()