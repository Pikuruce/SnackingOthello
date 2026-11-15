
from pathlib import Path
from direct.task import Task
from lib.src.composables.component_base import ComponentBase
from lib.src.components.sprite_animator import SpriteAnimator
import lib.utils.asset_path as path
from panda3d.core import (
    CardMaker,
    TransparencyAttrib,
    ClockObject,
    TextNode,
    FontPool,
)

class Sticker(ComponentBase):
    def __init__(
        self,
        base,
        name: str,
        is_two_sided: bool = True,
    ) -> None:
        super().__init__(base, name)

        self.base = base

        # 画面上の2D空間に配置する
        self.node.reparentTo(base.foreground_root)
        self.parent = base.foreground_root

        self.is_two_sided = is_two_sided

        # スプライトシートを読み込む
        self.model, json_data = self.loadModel()

        self.animator = SpriteAnimator(
            self.model,
            name,
            json_data,
        )

        self.clock = ClockObject.get_global_clock()

        # テキスト表示関連
        self.text_page: list[str] = []
        self.page_index = 0

        self.text = ""
        self.display_index = 0
        self.text_scroll_interval = 0.1
        self.elapsed_time = 0.0

        self.is_showing = False

        # ページ遷移の待機時間
        self.down_time = 2.2
        self.phase_elapsed = 0.0

        # ページの状態
        self.phase = "idle"

        self.task_name = ""

        self.game_font = FontPool.loadFont(path.fontFile())

        self.text_display = TextNode(f"{name}_text")
        self.text_display.setText("")
        self.text_display.setFont(self.game_font)
        self.text_display.setTextColor(0, 0, 0, 1)
        self.text_display.setAlign(TextNode.ALeft)

        self.text_display_np = self.node.attachNewNode(
            self.text_display
        )

        self.model.setBin("fixed", 1)
        self.text_display_np.setBin("fixed", 2)

    def loadModel(self):
        """
        画面上に表示するスプライトシートを読み込む
        """

        image_path, json_data = path.characterPath(self.name)

        file_path = Path(image_path.toOsSpecific())
        if not file_path.is_file():
            raise FileNotFoundError(
                f"Sticker image not found: {file_path}"
            )

        texture = self.loader.loadTexture(image_path)
        if texture is None:
            raise RuntimeError(
                f"Failed to load sticker texture: {image_path}"
            )

        card_maker = CardMaker(self.name)
        card_maker.setFrame(-0.5, 0.5, 0.0, 1.0)

        model = self.node.attachNewNode(
            card_maker.generate()
        )

        model.setTexture(texture)
        model.setTwoSided(self.is_two_sided)
        model.setTransparency(TransparencyAttrib.MAlpha)

        return model, json_data

    def playAnimation(
        self,
        direction: str,
        motion: str,
        loop: bool = True,
    ) -> bool:
        """
        アニメーションの再生
        """
        return self.animator.play(
            direction,
            motion,
            loop,
        )

   
    def setTextPos(self, x: float, y: float, z: float) -> None:
        """
        テキストの位置を設定
        """
        self.text_display_np.setPos(x, y, z)

    def setTextScale(self, x: float, y: float = None, z: float = None) -> None:
        """
        テキストの大きさを設定
        """
        if y is None or z is None:
            self.text_display_np.setScale(x)
        else:
            self.text_display_np.setScale(x, y, z)

    def setTextAnchor(self, anchor) -> None:
        """
        テキストのアンカーを設定
        """
        self.text_display.setAlign(anchor)

    def setText(self, text_page: list[str]) -> None:
        """
        テキストの内容を設定、1ページはリストの1要素分
        """
        self.base.taskMgr.remove(self.task_name)

        self.text_page = text_page
        self.page_index = 0

        self.elapsed_time = 0.0
        self.phase_elapsed = 0.0

        self.is_showing = False
        self.phase = "idle"

        self.text = ""
        self.display_index = 0

        self.text_display.setText("")

    def startPage(self) -> None:
        """
        ページインデックス設定後に文字列の頭にポインターを合わせる
        """
        self.text = self.text_page[self.page_index]

        self.display_index = 0
        self.elapsed_time = 0.0
        self.phase_elapsed = 0.0

        self.is_showing = bool(self.text)
        self.phase = "scrolling"

        self.text_display.setText("")

        self.show()

    def startTextScroll(self, task_name: str) -> None:
        """
        テキストのスクロールをはじめる
        """
        self.task_name = task_name

        self.base.taskMgr.remove(self.task_name)

        if not self.text_page:
            self.hide()
            return

        self.startPage()

        self.base.taskMgr.add(
            self.displayText,
            self.task_name,
        )

    def showAll(self) -> None:
        """
        スクロール中のテキストの一括表示
        """
        if self.phase != "scrolling":
            return

        self.display_index = len(self.text)
        self.elapsed_time = 0.0
        self.is_showing = False

        self.text_display.setText(self.text)

        self.phase = "visible_wait"
        self.phase_elapsed = 0.0

    def displayText(self, task: Task) -> Task:
        """
        テキストのスクロールをする
        """
        dt = self.clock.getDt()

        if self.phase == "scrolling":
            self.elapsed_time += dt

            count = int(
                self.elapsed_time / self.text_scroll_interval
            )

            if count > 0:
                self.elapsed_time -= (
                    count * self.text_scroll_interval
                )

                self.display_index = min(
                    self.display_index + count,
                    len(self.text),
                )

                self.text_display.setText(
                    self.text[:self.display_index]
                )

                self.base.playTextScroll()

            if self.display_index >= len(self.text):
                self.phase = "visible_wait"
                self.phase_elapsed = 0.0

        elif self.phase == "visible_wait":
            self.phase_elapsed += dt

            if self.phase_elapsed >= self.down_time:
                self.page_index += 1

                # 次のページがない場合
                if self.page_index >= len(self.text_page):
                    self.text = ""
                    self.text_display.setText("")
                    self.phase = "idle"
                    self.hide()
                    return task.done

                # 次のページを表示
                self.startPage()

        return task.cont

    def skip(self) -> None:
        """
        スクロール中なら一括表示、そうでないなら次のページ or 終了
        """
        # 文字送り中なら全文を表示
        if self.phase == "scrolling":
            self.showAll()
            return

        # 全文表示後の待機中なら次のページへ
        if self.phase == "visible_wait":
            self.page_index += 1

            # 次のページがない場合
            if self.page_index >= len(self.text_page):
                self.text = ""
                self.display_index = 0
                self.text_display.setText("")
                self.hide()
                return

            # 次のページがある場合
            self.startPage()


    def isHidden(self) -> bool:
        """
        非表示であるかどうか
        """
        return self.model.isHidden()

    def update(self, dt: float) -> None:
        """
        更新処理
        """
        super().update(dt)

        if not self.is_showing and not self.isHidden():
            self.elapsed_time += dt
            if self.elapsed_time >= self.down_time:
                self.hide()
                self.text = ""

        if self.animator is not None:
            self.animator.update(dt)

    def hide(self) -> None:
        """
        非表示に設定
        """
        self.base.taskMgr.remove(self.task_name)

        super().hide()
        self.text_display_np.hide()

        self.elapsed_time = 0.0
        self.phase_elapsed = 0.0
        self.is_showing = False
        self.phase = "idle"


    def show(self) -> None:
        """
        表示する
        """
        super().show()
        self.text_display_np.show()


    def remove(self) -> None:
        """
        削除する
        """
        self.base.taskMgr.remove(self.task_name)
        super().remove()