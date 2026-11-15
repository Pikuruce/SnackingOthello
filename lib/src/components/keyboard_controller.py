from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase
from typing import Callable
from panda3d.core import ClockObject

class KeyboardController(DirectObject):
    def __init__(self, base: ShowBase) -> None:
        self.base = base

        self.permission = True
        
        # 現在のキーの状態を保持する辞書
        self.keys = {}
        self.functions = {}
        
        # 長押し管理用の辞書
        self.hold_timers = {}
        self.repeat_intervals = {}
        self.press_times = {}
        self.last_repeat_times = {}

        self.ignore_until_release = set()
        
        # グローバルクロックの取得
        self.clock = ClockObject.get_global_clock()
        
        # 長押しを監視するバックグラウンドタスクを開始
        base.taskMgr.add(self.monitorHoldTask, "keyboard_hold_monitor")

    def setKeyEvent(self, key: str, action: str, func: Callable, hold_time: float = 0.5, repeat_interval: float = 0.1) -> None:
        """
        特定のキーに対してアクション名を設定する
        """
        self.keys[action] = False
        self.functions[action] = func
        self.hold_timers[action] = hold_time
        self.repeat_intervals[action] = repeat_interval
        self.press_times[action] = 0.0
        self.last_repeat_times[action] = 0.0
        
        # イベントの再登録
        self.accept(key, self.setKey, [action, True])
        self.accept(f"{key}-up", self.setKey, [action, False])

    def setKey(self, action: str, is_pressed: bool) -> None:
        """
        キー入力イベント
        """
        if action in self.ignore_until_release:
            if not is_pressed:
                self.ignore_until_release.discard(action)
            return

        current_time = self.clock.get_frame_time()

        if is_pressed:
            if not self.keys[action]:
                self.keys[action] = True
                self.press_times[action] = current_time
                self.last_repeat_times[action] = current_time
                self.onSinglePress(action)
        else:
            self.keys[action] = False
            self.press_times[action] = 0.0
            self.last_repeat_times[action] = 0.0

    def ignoreNextPress(self, action: str) -> None:
        """
        次の入力を無効かする
        """
        self.keys[action] = False
        self.press_times[action] = 0.0
        self.last_repeat_times[action] = 0.0
        self.ignore_until_release.add(action)

    def setActionFunction(self, action: str, func: Callable) -> None:
        """
        特定のアクションに対して関数を登録する
        """
        if action in self.functions:
            self.functions[action] = func
        else:
            raise ValueError(f"Action '{action}' is not defined in key_map.")
        
    def monitorHoldTask(self, task):
        """
        毎フレーム実行され、長押し状態を判定するタスク
        """
        current_time = self.clock.get_frame_time()
        
        for action, is_down in self.keys.items():
            if is_down:
                elapsed = current_time - self.press_times[action]
                
                # 1. 最初に長押し基準（0.5秒）を超えたか判定
                if elapsed >= self.hold_timers[action]:
                    # 2. 前回の実行から一定間隔（0.1秒）が経ったか判定
                    time_since_repeat = current_time - self.last_repeat_times[action]
                    
                    # 最初にホールド状態に入った瞬間、またはインターバル経過時
                    if self.last_repeat_times[action] == self.press_times[action] or time_since_repeat >= self.repeat_intervals[action]:
                        self.onHoldRepeat(action)
                        self.last_repeat_times[action] = current_time
                        
        return task.cont

    def isPressed(self, action: str) -> bool:
        """
        現在のキーの純粋な押下状態（押しっぱなし含む）
        """
        return self.keys.get(action, False)

    def onSinglePress(self, action: str) -> None:
        """
        キーが押された瞬間に1度だけ呼ばれる
        """
        if self.functions[action] and self.permission:
            self.functions[action]()

    def onHoldRepeat(self, action: str) -> None:
        """
        長押しと判定され、かつリピート間隔ごとに呼ばれる
        """
        if self.functions[action] and self.permission:
            self.functions[action]()

    def setPermission(self, permission: bool) -> None:
        """
        入力イベントの発火許可設定
        """
        self.permission = permission

    def destroy(self) -> None:
        """
        クラス破棄時のクリーンアップ
        """
        self.base.taskMgr.remove("keyboard_hold_monitor")
        self.ignoreAll()
