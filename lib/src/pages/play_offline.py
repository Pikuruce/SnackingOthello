from lib.src.composables.play_base import PlayBase

class PlayOffline(PlayBase):
    def __init__(self, base) -> None:
        super().__init__(base)

        self.keyboard_controller.setKeyEvent("arrow_up", "up", lambda: self.pointerMove(1, 0), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("arrow_down", "down", lambda: self.pointerMove(-1, 0), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("arrow_left", "left", lambda: self.pointerMove(0, -1), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("arrow_right", "right", lambda: self.pointerMove(0, 1), hold_time=0.3)
        self.keyboard_controller.setKeyEvent("enter", "enter", self.enter)
        self.keyboard_controller.setKeyEvent("escape", "menu", self.openMenu)

        self.menu.addItem("もどる", self.endGame)

        self.gameover.addItem("リトライ", self.restartGame)
        self.gameover.addItem("しゅうりょう", self.endGame)