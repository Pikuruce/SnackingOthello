from lib.src.components.object import Object
from lib.src.components.character import Character
from lib.src.components.sticker import Sticker
from lib.src.components.othello_board import OthelloBoard
from lib.src.components.keyboard_controller import KeyboardController
from lib.src.components.select_screen import SelectScreen
from direct.task import Task
import lib.utils.asset_path as path
import datetime, json
from panda3d.core import ClockObject, TextNode, AudioSound, FontPool, CardMaker, TransparencyAttrib

class PlayBase:
    def __init__(self, base) -> None:
        self.base = base

        self.select_pointer = [0, 0]

        self.clock = ClockObject.get_global_clock()

        self.is_clear = False
        self.no_save = False

        self.game_font = FontPool.loadFont(path.fontFile())

        self.objects = []

        table = Object(self.base, "SnackingOthello_Table")
        table.setPos(-16, -32, 0)
        self.objects.append(table)

        self.othello_board = OthelloBoard(self.base)
        for i in range(4):
            for j in range(4):
                floor = Object(self.base, "SnackingOthello_Floor")
                floor.setPos((i - 2) * 32, (j - 2) * 32, -1)
                self.objects.append(floor)
        for i in range(4):
            if i == 2:
                wall = Object(self.base, "SnackingOthello_Window")
                wall.setPos((i - 2) * 32, 47, 0)
                self.objects.append(wall)
            else:
                wall = Object(self.base, "SnackingOthello_Wall")
                wall.setPos((i - 2) * 32, 47, 0)
                self.objects.append(wall)

        wateringcan = Object(self.base, "SnackingOthello_WateringCan")
        wateringcan.setScale(0.2, 0.2, 0.2)
        wateringcan.setPos(-7, 47, 15)
        wateringcan.setRotate(-45, 0, 0)
        self.objects.append(wateringcan)

        self.flower = Character(self.base, "Dance_Flower", True)
        self.flower.setScale(10, 10, 10)
        self.flower.setPos(5, 47, 15)
        self.flower.playAnimation("front", "dance")
        self.objects.append(self.flower)

        self.silky = Character(self.base, "SnackingOthello_Silky", True)
        self.silky.setScale(27, 28, 28)
        self.silky.setPos(-5, -18, 0)
        self.silky.playAnimation("front", "idle")
        self.objects.append(self.silky)

        self.buliot = Character(self.base, "SnackingOthello_Buliot", True)
        self.buliot.setScale(28, 28, 28)
        self.buliot.setPos(-27, -18, 0)
        self.buliot.playAnimation("front", "idle")
        self.objects.append(self.buliot)

        plate_image_path = path.imagePath("SnackingOthello_Plate.png")
        plate_image = self.base.loader.loadTexture(plate_image_path)

        card = CardMaker("title-image")
        card.setFrame((-0.5, 0.5, -0.5, 0.5))

        self.plate_np = self.base.foreground_root.attachNewNode(
            card.generate()
        )
        self.plate_np.setTexture(plate_image)
        self.plate_np.setTransparency(TransparencyAttrib.MAlpha)
        self.plate_np.setPos(0, 0, 0.3)
        self.plate_np.setScale(0.65, 1, 0.5)

        # Plateを先に描画
        self.plate_np.setBin("fixed", 0)
        self.plate_np.setDepthTest(False)
        self.plate_np.setDepthWrite(False)

        self.silky_stomach = Sticker(self.base, "SnackingOthello_Stomach")
        self.silky_stomach.setScale(0.2, 0.2, 0.2)
        self.silky_stomach.setPos(0.2, 0, 0.3)
        self.silky_stomach.setTextPos(0, 0, -0.8)
        self.silky_stomach.setTextScale(0.5)
        self.silky_stomach.setTextAnchor(TextNode.ACenter)
        self.silky_stomach.setText([f"0/{self.othello_board.max_eat}"])
        self.silky_stomach.startPage()
        self.silky_stomach.showAll()
        self.objects.append(self.silky_stomach)

        self.buliot_stomach = Sticker(self.base, "SnackingOthello_Stomach")
        self.buliot_stomach.setScale(0.2, 0.2, 0.2)
        self.buliot_stomach.setPos(-0.2, 0, 0.3)
        self.buliot_stomach.setTextPos(0, 0, -0.8)
        self.buliot_stomach.setTextScale(0.5)
        self.buliot_stomach.setTextAnchor(TextNode.ACenter)
        self.buliot_stomach.setText([f"0/{self.othello_board.max_eat}"])
        self.buliot_stomach.startPage()
        self.buliot_stomach.showAll()
        self.objects.append(self.buliot_stomach)
        
        self.base.cam.setPos(-16, -75, 40)
        self.base.cam.lookAt(-16, 8, 6)
        self.danceFlowerUpdate()

        self.menu = SelectScreen(self.base)
        self.menu.addItem("つづける", self.closeMenu)
        self.menu.addItem("BGM", self.toggleBGM)
        self.menu.addItem("SE", self.toggleSE)
        self.menu.setExplain("ポーズ")

        self.updateAudioMenu()

        self.gameover = SelectScreen(self.base)
        self.gameover.setScreenColor(0, 0, 0, 0.2)

        self.keyboard_controller = KeyboardController(self.base)

        self.base.taskMgr.add(self.update, "game_update")

    def pointerMove(self, dx: int, dy: int) -> None:
        """
        ポインターを動かす
        """
        self.select_pointer[0] = (self.select_pointer[0] + dx) % 8
        self.select_pointer[1] = (self.select_pointer[1] + dy) % 8
        self.othello_board.setArrowPos(self.select_pointer[0], self.select_pointer[1])
        self.base.playCookieSelect()

    def enter(self) -> None:
        """
        決定ボタン処理
        """
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
            if self.othello_board.restartCheck():
                self.silky.playAnimation("front", "eat")
                self.buliot.playAnimation("front", "eat")

        self.updateStomach()

    def openMenu(self) -> None:
        """
        メニューを開く
        """
        self.keyboard_controller.setPermission(False)
        self.menu.openScreen()

    def closeMenu(self) -> None:
        """
        メニューを閉じる
        """
        self.menu.closeScreen()
        self.keyboard_controller.ignoreNextPress("enter")
        self.keyboard_controller.setPermission(True)

    def openGameover(self) -> None:
        """
        終了画面を開く
        """
        self.keyboard_controller.setPermission(False)
        self.gameover.openScreen()

    def restartGame(self) -> None:
        """
        ゲームをはじめからやりなおす
        """
        self.is_clear = False
        self.othello_board.resetGame()
        self.menu.closeScreen()
        self.gameover.closeScreen()
        self.keyboard_controller.setPermission(True)
        self.updateStomach()
        if self.base.bgm.status() == AudioSound.READY:
            self.base.playBGM()

    def endGame(self) -> None:
        """
        ゲームを終了しタイトルに戻る
        """
        self.base.taskMgr.remove("game_update")
        self.keyboard_controller.ignoreNextPress("enter")
        self.keyboard_controller.destroy()
        self.othello_board.destroy()
        while self.objects:
            obj = self.objects.pop()
            obj.remove()
        self.silky_stomach.remove()
        self.buliot_stomach.remove()
        self.plate_np.removeNode()
        self.gameover.closeScreen()
        self.menu.closeScreen()
        self.base.title.openScreen()
        self.base.title_np.show()
        self.base.playBGM(scale=0.5)

    def updateStomach(self) -> None:
        """
        満腹度の更新
        """
        w = str(min(self.othello_board.getWhiteRatio(), 8))
        b = str(min(self.othello_board.getBlackRatio(), 8))
        self.silky_stomach.playAnimation("front", w, loop=False)
        self.buliot_stomach.playAnimation("front", b, loop=False)
        self.silky_stomach.setText([f"{self.othello_board.w_eat}/{self.othello_board.max_eat}"])
        self.silky_stomach.startPage()
        self.silky_stomach.showAll()
        self.buliot_stomach.setText([f"{self.othello_board.b_eat}/{self.othello_board.max_eat}"])
        self.buliot_stomach.startPage()
        self.buliot_stomach.showAll()

    def saveReplay(self) -> None:
        """
        リプレイを保存
        """
        save_dir = path.getSaveDirectory()
        save_dir.mkdir(parents=True, exist_ok=True)

        # 既存のリプレイを取得（古い順）
        replay_files = sorted(
            save_dir.glob("replay_*.json"),
            key=lambda p: p.stat().st_mtime
        )

        # 4件以上ある場合、古いものを削除
        while len(replay_files) >= 4:
            old_file = replay_files.pop(0)
            old_file.unlink()

        # 新しいリプレイを保存
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        save_path = save_dir / f"replay_{now}.json"

        data = {
            "version": self.base.version,
            "winner": self.othello_board.winner,
            "max_eat": self.othello_board.max_eat,
            "moves": self.othello_board.getSaveData(),
        }

        with save_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def update(self, task: Task) -> Task:
        """
        更新処理
        """
        dt = self.clock.getDt()
        self.flower.animator.update(dt)
        if self.othello_board.update(dt) and not self.othello_board.is_eating:
            if self.othello_board.turn == "B":
                self.silky.playAnimation("front", "idle")
            else:
                self.buliot.playAnimation("front", "idle")

        if self.othello_board.is_eating:
            self.updateStomach()

        winner = self.othello_board.winner
        if winner == "B" and not self.othello_board.is_eating and not self.othello_board.is_flipping and not self.is_clear:
            self.is_clear = True
            if not self.no_save:
                self.saveReplay()
            self.buliot.playAnimation("front", "smile")
            self.gameover.setExplain("くろねこ　マンプク")
            self.openGameover()
            self.base.playEnd()
            self.base.stopBGM()
        elif winner == "W" and not self.othello_board.is_eating and not self.othello_board.is_flipping and not self.is_clear:
            self.is_clear = True
            if not self.no_save:
                self.saveReplay()
            self.silky.playAnimation("front", "smile")
            self.gameover.setExplain("しろねこ　マンプク")
            self.openGameover()
            self.base.playEnd()
            self.base.stopBGM()

        self.silky.update(dt)
        self.buliot.update(dt)
        return task.cont

    def updateAudioMenu(self) -> None:
        """
        BGMとSEのオンオフのテキストの設定
        """
        self.menu.setText(
            1,
            f"BGM: {'ON' if self.base.bgm_permission else 'OFF'}"
        )
        self.menu.setText(
            2,
            f"SE: {'ON' if self.base.se_permission else 'OFF'}"
        )


    def toggleBGM(self) -> None:
        """
        BGMのオンオフ切り替え
        """
        self.base.bgm_permission = not self.base.bgm_permission

        self.danceFlowerUpdate()

        if self.base.bgm_permission:
            self.base.unmuteBGM()
        else:
            self.base.muteBGM()

        self.updateAudioMenu()


    def toggleSE(self) -> None:
        """
        SEのオンオフ切り替え
        """
        self.base.se_permission = not self.base.se_permission

        self.updateAudioMenu()

        self.base.playSETest()

    def danceFlowerUpdate(self) -> None:
        """
        BGMに合わせて花の状態を更新
        """
        if self.base.bgm_permission:
            self.flower.playAnimation("front", "dance")
        else:
            self.flower.playAnimation("front", "idle")
