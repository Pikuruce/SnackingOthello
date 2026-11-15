from direct.gui.OnscreenImage import OnscreenImage
import lib.utils.asset_path as path
from lib.src.components.keyboard_controller import KeyboardController
from direct.gui.OnscreenText import OnscreenText
from typing import Callable
from panda3d.core import (
    TextNode,
    FontPool,
    CardMaker
)

class SelectScreen:
    def __init__(self, base) -> None:
        self.base = base

        self.pointer = -1

        self.game_font = FontPool.loadFont(path.fontFile())
        
        fgdr=self.base.foreground_dr

        cm = CardMaker("screen")
        cm.setFrame(-1, 1, -1, 1)

        self.screen = self.base.foreground_root.attachNewNode(cm.generate())
        self.screen.setColor(0, 0, 0, 0.5)
        self.screen.setTransparency(True)
        self.screen.setDepthTest(False)
        self.screen.setDepthWrite(False)

        # 描画順を最前面にする
        self.screen.setBin("fixed", 10)

        self.explain_text = OnscreenText(
            text="explain",
            parent=self.screen,
            pos=(0, 0.7),
            scale=0.22,
            fg=(1, 1, 0, 1),
            font=self.game_font,
            align=TextNode.ACenter,
            mayChange=True,
        )

        self.controll_explain1 = OnscreenText(
            text=f"バージョン:{self.base.version}\n操作方法\nF11: 全画面表示\n\n\nタイトル・メニュー画面\n十字キー: ポインター移動\nEnter: 決定\n\nゲーム中\n十字キー: ポインター移動\nEnter: 決定\nEscape: メニュー表示",
            parent=self.screen,
            pos=(0.7, -0.25),
            scale=0.04,
            fg=(1, 1, 0, 1),
            font=self.game_font,
            align=TextNode.ACenter,
            mayChange=True,
        )

        self.items: list[OnscreenText] = []
        self.funcs: list[Callable[[], None] | None] = []

        self.keyboard_controller = KeyboardController(self.base)

        self.keyboard_controller.setKeyEvent(
            "w", "up", lambda: self.pointerMove(-1)
        )
        self.keyboard_controller.setKeyEvent(
            "arrow_up", "up", lambda: self.pointerMove(-1)
        )
        self.keyboard_controller.setKeyEvent(
            "s", "down", lambda: self.pointerMove(1)
        )
        self.keyboard_controller.setKeyEvent(
            "arrow_down", "down", lambda: self.pointerMove(1)
        )
        self.keyboard_controller.setKeyEvent(
            "enter", "select", self.selectItem
        )

        self.closeScreen()

    def pointerMove(self, d: int) -> None:
        """
        選択位置を移動する
        """

        if not self.items:
            return

        self.pointer = (self.pointer + d) % len(self.items)

        self.updateItems()

        self.base.playTextSelect()

    def addItem(
        self,
        text: str,
        func: Callable[[], None] | None = None
    ) -> None:
        """
        メニュー項目と対応する関数を追加する
        """

        item = OnscreenText(
            text=text,
            parent=self.screen,
            pos=(0, -0.2 * len(self.items)),
            scale=0.07,
            fg=(1, 1, 0, 1),
            font=self.game_font,
            align=TextNode.ACenter,
            mayChange=True,
        )

        self.items.append(item)
        self.funcs.append(func)

        self.updateItems()


    def removeItem(self, num: int) -> None:
        """
        指定したメニュー項目と対応する関数を削除する
        """

        if not 0 <= num < len(self.items):
            return

        self.items[num].destroy()

        self.items.pop(num)
        self.funcs.pop(num)

        if self.items:
            if num < self.pointer:
                self.pointer -= 1
            elif self.pointer >= len(self.items):
                self.pointer = len(self.items) - 1
        else:
            self.pointer = 0

        self.updateItems()


    def clearItems(self) -> None:
        """
        すべてのメニュー項目を削除する
        """

        for item in self.items:
            item.destroy()

        self.items.clear()
        self.funcs.clear()
        self.pointer = -1


    def setText(self, num: int, text: str) -> None:
        """
        指定したメニュー項目の文字列を変更する
        """

        if not 0 <= num < len(self.items):
            return

        self.items[num].setText(text)

    def setExplain(self, text: str) -> None:
        """
        画面上の説明文を設定
        """
        self.explain_text.setText(text)

    def setScreenColor(self, r: float, g: float, b: float, a: float) -> None:
        """
        パネルの色を指定
        """
        self.screen.setColor(r, g, b, a)


    def selectItem(self) -> None:
        """
        現在選択している項目の関数を実行する
        """

        if not self.items or self.pointer < 0:
            return

        func = self.funcs[self.pointer]

        if func is not None:
            self.base.playTextSelect()
            func()


    def updateItems(self) -> None:
        """
        項目の位置と選択色を更新する
        """

        for i, item in enumerate(self.items):
            item.setPos(0, -0.2 * i)

            if i == self.pointer:
                item.setFg((1, 0, 0, 1))
            else:
                item.setFg((1, 1, 0, 1))    

    def closeScreen(self) -> None:
        """
        この画面を閉じる
        """
        self.keyboard_controller.setPermission(False)
        self.screen.hide()
        self.pointer = -1

    def openScreen(self) -> None:
        """
        この画面を開く
        """
        self.keyboard_controller.setPermission(True)
        self.screen.show()
        self.updateItems()

    def loadImage(self, image_name: str, scale: tuple[float, float, float]) -> OnscreenImage:
        """
        背景や前景読み込み用関数
        """
        img_path = path.imagePath(image_name)
        if not img_path.exists():
            raise FileNotFoundError(f"Image file not found: {img_path}")

        texture = self.base.loader.loadTexture(img_path)
        if texture is None:
            raise RuntimeError(f"Texture loading failed: {img_path}")
        
        return OnscreenImage(image=texture, scale=scale)