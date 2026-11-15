from lib.src.pages.play_replay import PlayReplay
from lib.src.components.sticker import Sticker
from direct.task import Task

class Tutorial(PlayReplay):
    def __init__(self, base, json_data) -> None:
        super().__init__(base, json_data)
        self.explain_text.setText("auto progress")
        self.dialogue = Sticker(self.base, "SnackingOthello_SpeechPlate")
        self.dialogue.setPos(0, 0, -1)
        self.dialogue.setScale(1.5, 1.0, 1.0)
        self.dialogue.setTextPos(-0.4, -0.01, 0.75)
        self.dialogue.setTextScale(0.08)
        self.dialogue.hide()
        self.dialogue_showing = False
        self.dialogue_progress_interval = 0.7
        self.elapsed_time = 0.0
        self.keyboard_controller.setKeyEvent("enter", "enter", self.dialogue.skip)
        self.base.taskMgr.add(self.autoPlay, "auto")

    def autoPlay(self, task: Task) -> Task:
        dt = self.clock.getDt()
        self.elapsed_time += dt
        self.dialogue.update(dt)
        if self.gameover.keyboard_controller.permission:
            return task.done
        if self.menu.keyboard_controller.permission:
            return task.cont

        if self.elapsed_time >= self.dialogue_progress_interval:
            self.elapsed_time = 0
            self.next()
        return task.cont

    def endGame(self) -> None:
        self.base.taskMgr.remove("auto")
        self.dialogue.remove()
        super().endGame()

    def next(self) -> None:
        if self.current_move_index == 16:
            self.dialogue_progress_interval = 0.0
        if self.dialogue_showing and self.dialogue.isHidden():
            self.dialogue_showing = False
            self.current_move_index = min(self.current_move_index + 1, len(self.moves) - 1)

        if type(self.moves[self.current_move_index][0]) == str and self.dialogue.isHidden():
            texts = self.moves[self.current_move_index]
            if texts[0] == "silky":
                direction, motion = self.buliot.getAnimation()
                if direction == "front" and motion == "meow":
                    self.buliot.playAnimation("front", "idle")
                self.silky.playAnimation("front", "meow")
            elif texts[0] == "buliot":
                direction, motion = self.silky.getAnimation()
                if direction == "front" and motion == "meow":
                    self.silky.playAnimation("front", "idle")
                self.buliot.playAnimation("front", "meow")

            self.dialogue.setText(texts[1])
            self.dialogue.startTextScroll("dialogue")
            self.dialogue_showing = True

        elif not self.dialogue_showing and self.dialogue.isHidden():
            super().next()