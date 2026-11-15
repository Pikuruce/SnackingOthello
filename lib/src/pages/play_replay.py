from lib.src.composables.play_base import PlayBase
from panda3d.core import TextNode

class PlayReplay(PlayBase):
    def __init__(self, base, json_data) -> None:
        super().__init__(base)
        self.varsion: int = json_data["version"]
        self.max_eat: int = json_data["max_eat"]
        self.moves: list[list[int]] = json_data["moves"]
        self.current_move_index: int = 0
        self.current_act: str = "pointer"
        self.no_save = True
        self.othello_board.setMaxeat(self.max_eat)
        self.keyboard_controller.setKeyEvent("enter", "enter", self.next)
        self.keyboard_controller.setKeyEvent("escape", "menu", self.openMenu)

        self.menu.addItem("もどる", self.endGame)
        self.gameover.addItem("しゅうりょう", self.endGame)

        self.explain_text = TextNode("object_text")
        self.explain_text.setText("'enter' to next")
        self.explain_text.setFont(self.game_font)
        self.explain_text.setTextColor(1, 0, 0, 1)
        self.explain_text.setAlign(TextNode.ACenter)

        self.explain_text_np = self.base.render.attachNewNode(self.explain_text)
        self.explain_text_np.setPos(-16, -18, 16)
        self.explain_text_np.setScale(1.0)

    def next(self) -> None:
        if not self.othello_board.canAct() or self.menu.keyboard_controller.permission:
            return
        pos = self.moves[self.current_move_index]
        if self.current_act == "pointer":
            self.current_act = "enter"
            self.select_pointer = pos
            self.othello_board.setArrowPos(self.select_pointer[0], self.select_pointer[1])
        elif self.current_act == "enter":
            self.enter()
            self.current_act = "pointer"
            self.current_move_index = min(self.current_move_index + 1, len(self.moves) - 1)

    def endGame(self) -> None:
        self.explain_text_np.removeNode()
        super().endGame()
