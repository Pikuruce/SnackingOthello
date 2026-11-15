from direct.gui.DirectGui import DirectEntry
from panda3d.core import TextNode


class TextInput:
    def __init__(
        self,
        base,
        pos=(0, 0, 0.2),
        scale=0.1,
        width=8,
        sort_order=100,
        parent=None
    ) -> None:
        self.base = base

        self.entry = DirectEntry(
            parent=parent or base.aspect2d,
            text="",
            scale=scale,
            pos=pos,
            width=width,
            numLines=1,
            focus=0,
            sortOrder=sort_order,
            frameColor=(1, 1, 1, 1),
            text_fg=(0, 0, 0, 1),
            text_align=TextNode.ACenter,
        )

    def getText(self) -> str:
        """
        打ち込まれたテキストを返す
        """
        return self.entry.get()

    def setText(self, text: str) -> None:
        """
        テキストを入力する
        """
        self.entry.enterText(text)

    def setFocus(self, focus: bool) -> None:
        """
        フォーカスを設定
        """
        self.entry["focus"] = focus

    def setPos(self, pos) -> None:
        """
        位置を設定
        """
        self.entry.setPos(*pos)

    def show(self) -> None:
        """
        表示する
        """
        self.entry.show()

    def hide(self) -> None:
        """
        非表示にする
        """
        self.entry.hide()

    def close(self) -> None:
        """
        閉じる（破棄する）
        """
        self.entry.destroy()