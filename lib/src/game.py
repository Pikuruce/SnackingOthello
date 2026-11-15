from direct.showbase.ShowBase import ShowBase
import lib.utils.asset_path as path
import lib.utils.app_config as ac
from lib.src.components.select_screen import SelectScreen
from lib.src.pages.play_offline import PlayOffline
from lib.src.pages.play_online import PlayOnline
from lib.src.pages.tutorial import Tutorial
import json
from lib.src.pages.play_replay import PlayReplay

from panda3d.core import (
    AudioSound,
    Camera,
    NodePath,
    OrthographicLens,
    WindowProperties,
    TransparencyAttrib,
    CardMaker
)


class SnackingOthello(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()

        self.version = ac.getVersion()

        # ウィンドウ設定
        window_config = ac.getWindowConfig()

        self.fullscreen = window_config["fullscreen"]
        self.window_size = (
            window_config["size"][0],
            window_config["size"][1]
        )

        props = WindowProperties()
        width, height = self.window_size
        props.setSize(width, height)

        self.accept("f11", self.switchFullscreen)

        if window_config.get("fullscreen", False):
            self.switchFullscreen()

        ratio = window_config["ratio"]
        self.target_aspect = ratio[0] / ratio[1]

        self.camLens.setFov(40)
        self.setAspectRatio(self.target_aspect)

        self.display_region = self.cam.node().getDisplayRegion(0)
        self.display_region_2d = self.cam2d.node().getDisplayRegion(0)

        self.win.setClearColor((0, 0, 0, 1))
        self.win.setClearColorActive(True)

        self.display_region.setClearColor((0, 1, 1, 1))
        self.display_region.setClearColorActive(True)

        # Foreground Camera
        self.foreground_lens = OrthographicLens()
        self.foreground_lens.setFilmSize(
            2 * self.target_aspect,
            2
        )
        self.foreground_lens.setNearFar(-1000, 1000)

        self.foreground_cam = Camera("foreground")
        self.foreground_cam.setLens(self.foreground_lens)

        # Foreground専用シーン
        self.foreground_root = NodePath("foreground-root")
        self.foreground_cam.setScene(self.foreground_root)

        self.foreground_np = self.render.attachNewNode(self.foreground_cam)

        self.foreground_dr = self.win.makeDisplayRegion()
        self.foreground_dr.setCamera(self.foreground_np)
        self.foreground_dr.setSort(100)
        self.foreground_dr.setClearDepthActive(False)
        self.foreground_dr.setClearColorActive(False)

        title_image_path = path.imagePath("SnackingOthello_Title.png")
        title_image = self.loader.loadTexture(title_image_path)

        card = CardMaker("title-image")
        card.setFrame(
            -self.target_aspect,
            self.target_aspect,
            -1,
            1
        )

        self.title_np = self.foreground_root.attachNewNode(
            card.generate()
        )
        self.title_np.setTexture(title_image)
        self.title_np.setTransparency(TransparencyAttrib.MAlpha)
        self.title_np.setPos(0, 0, 0)

        # TextInput専用DisplayRegion
        self.input_dr = self.win.makeDisplayRegion()
        self.input_dr.setSort(110)
        self.input_dr.setClearDepthActive(False)
        self.input_dr.setClearColorActive(False)
        self.input_dr.setCamera(self.cam2d)

        self.accept("window-event", self.onWindowEvent)
        self.updateViewport()

        self.title_init = SelectScreen(self)
        self.title_init.addItem("十字とエンターで選んでね", self.openTitle)
        self.title_init.setExplain("")
        self.title_init.setScreenColor(0, 0, 0, 0)
        self.title_init.openScreen()

        self.title = SelectScreen(self)
        self.title.addItem("チュートリアル", self.startTutorial)
        self.title.addItem("スタート", self.openGameOpt)
        self.title.addItem("リプレイ", self.openReplay)
        self.title.addItem("せってい", self.openSettings)
        self.title.addItem("しゅうりょう", self.exit)
        self.title.setExplain("たべるオセロ")

        self.replay = SelectScreen(self)
        self.replay.setExplain("リプレイ")

        audio_config = ac.getAudioConfig()
        self.master_volume = audio_config["master_volume"]
        self.bgm_volume = audio_config["bgm_volume"]
        self.se_volume = audio_config["se_volume"]
        self.bgm_permission = audio_config["bgm"]
        self.se_permission = audio_config["se"]

        self.settings = SelectScreen(self)
        self.settings.addItem("もどる", self.closeSettings)
        self.settings.addItem(f"BGM: {'ON' if self.bgm_permission else 'OFF'}", self.setBGMSetting)
        self.settings.addItem(f"SE: {'ON' if self.se_permission else 'OFF'}", self.setSESetting)
        self.settings.setExplain("せってい")

        self.bgm = self.loader.loadSfx(path.bgmPath("daisy_bell.wav"))
        self.bgm.setLoop(True)
        self.bgm.setVolume(self.master_volume * self.bgm_volume)

        self.se_cookie_select = self.loader.loadSfx(path.sePath("cookie_select.wav"))
        self.se_cookie_select.setVolume(self.master_volume * self.se_volume)
        self.se_eat = self.loader.loadSfx(path.sePath("eat.wav"))
        self.se_eat.setVolume(self.master_volume * self.se_volume)
        self.se_end = self.loader.loadSfx(path.sePath("end.wav"))
        self.se_end.setVolume(self.master_volume * self.se_volume)
        self.se_test = self.loader.loadSfx(path.sePath("se_test.wav"))
        self.se_test.setVolume(self.master_volume * self.se_volume)
        self.se_text_select = self.loader.loadSfx(path.sePath("text_select.wav"))
        self.se_text_select.setVolume(self.master_volume * self.se_volume)
        self.se_text_scroll = self.loader.loadSfx(path.sePath("text_scroll.wav"))
        self.se_text_scroll.setVolume(self.master_volume * self.se_volume)

        self.game_option = SelectScreen(self)
        self.game_option.addItem("もどる", self.closeGameOpt)
        self.game_option.addItem("ローカル", self.startGame)
        self.game_option.addItem("ルーム作成", self.createRoom)
        self.game_option.addItem("ルーム参加", self.joinRoom)
        self.game_option.setExplain("たいせん")

        
        self.playBGM(scale=0.5)

    def switchFullscreen(self) -> None:
        next_full_screen = not self.fullscreen

        properties = WindowProperties()
        properties.setFullscreen(next_full_screen)

        if next_full_screen:
            properties.setSize(
                self.pipe.getDisplayWidth(),
                self.pipe.getDisplayHeight(),
            )
        else:
            properties.setSize(
                self.window_size[0],
                self.window_size[1],
            )

        self.win.requestProperties(properties)
        self.fullscreen = next_full_screen

    def onWindowEvent(self, window) -> None:
        ShowBase.windowEvent(self, window)

        if window == self.win and window.isValid():
            if not self.fullscreen:
                self.windowed_size = (
                    window.getXSize(),
                    window.getYSize()
                )

            self.setAspectRatio(self.target_aspect)
            self.updateViewport()


    def updateViewport(self) -> None:
        if self.win is None:
            return

        width = self.win.getXSize()
        height = self.win.getYSize()

        if width <= 0 or height <= 0:
            return

        aspect = width / height
        target = self.target_aspect

        if aspect > target:
            # 横長：左右に余白
            region_width = height * target / width
            left = (1.0 - region_width) / 2.0
            right = left + region_width

            dimensions = (left, right, 0.0, 1.0)

        else:
            # 縦長：上下に余白
            region_height = width / target / height
            bottom = (1.0 - region_height) / 2.0
            top = bottom + region_height

            dimensions = (0.0, 1.0, bottom, top)

        # 3Dと2Dの表示領域を同じサイズにする
        self.display_region.setDimensions(*dimensions)
        self.display_region_2d.setDimensions(*dimensions)
        self.foreground_dr.setDimensions(*dimensions)

    def playCookieSelect(self) -> None:
        if self.se_permission:
            self.se_cookie_select.play()

    def playEat(self) -> None:
        if self.se_permission:
            self.se_eat.play()

    def playEnd(self) -> None:
        if self.se_permission:
            self.se_end.play()

    def playSETest(self) -> None:
        if self.se_permission:
            self.se_test.play()

    def playTextSelect(self) -> None:
        if self.se_permission:
            self.se_text_select.play()

    def playTextScroll(self) -> None:
        if self.se_permission:
            self.se_text_scroll.play()

    def playBGM(self, scale: float = 1) -> None:
        if self.bgm_permission:
            self.bgm.setVolume(self.master_volume * self.bgm_volume * scale)
            if self.bgm.status() == AudioSound.READY:
                self.bgm.play()

    def stopBGM(self) -> None:
        self.bgm.stop()

    def muteBGM(self) -> None:
        self.bgm.setVolume(0)

    def unmuteBGM(self, scale: float = 1) -> None:
        self.bgm.setVolume(self.master_volume * self.bgm_volume * scale)
        
    def startTutorial(self) -> None:
        Tutorial(self, path.getReplay())
        self.playBGM()
        self.title.closeScreen()
        self.showTitleImage(False)

    def startGame(self) -> None:
        PlayOffline(self)
        self.playBGM()
        self.game_option.closeScreen()
        self.showTitleImage(False)

    def openReplay(self) -> None:
        self.title.closeScreen()

        # 前回の一覧を削除
        self.replay.clearItems()

        # 戻る項目
        self.replay.addItem("もどる", self.closeReplay)

        # 保存フォルダ内のJSONを取得
        save_dir = path.getSaveDirectory()

        replay_files = sorted(
            save_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not replay_files:
            self.replay.addItem("リプレイなし")
        else:
            for file in replay_files:
                try:
                    with file.open("r", encoding="utf-8") as f:
                        json_data = json.load(f)

                    # ファイル名を選択肢にする
                    self.replay.addItem(
                        file.stem,
                        lambda data=json_data: self.startReplay(data)
                    )

                except (json.JSONDecodeError, OSError) as e:
                    print(f"Failed to load replay: {file.name}: {e}")

        self.replay.openScreen()

    def closeReplay(self) -> None:
        self.replay.closeScreen()
        self.title.openScreen()


    def startReplay(self, json_data: dict) -> None:
        self.replay.closeScreen()
        PlayReplay(self, json_data)
        self.showTitleImage(False)

    def openSettings(self) -> None:
        self.title.closeScreen()
        self.settings.openScreen()

    def setBGMSetting(self) -> None:
        self.bgm_permission = not self.bgm_permission

        if self.bgm_permission:
            self.unmuteBGM(scale=0.5)
        else:
            self.muteBGM()

        self.settings.setText(
            1,
            f"BGM: {'ON' if self.bgm_permission else 'OFF'}"
        )


    def setSESetting(self) -> None:
        self.se_permission = not self.se_permission

        self.settings.setText(
            2,
            f"SE: {'ON' if self.se_permission else 'OFF'}"
        )

        self.playSETest()
    
    def exit(self) -> None:
        self.userExit()

    def closeSettings(self) -> None:
        self.settings.closeScreen()
        self.title.openScreen()

    def openGameOpt(self) -> None:
        self.title.closeScreen()
        self.game_option.openScreen()

    def closeGameOpt(self) -> None:
        self.game_option.closeScreen()
        self.title.openScreen()

    def createRoom(self) -> None:
        self.game_option.closeScreen()
        self.showTitleImage(False)
        PlayOnline(self, is_host=True)


    def joinRoom(self) -> None:
        self.game_option.closeScreen()
        self.showTitleImage(False)
        PlayOnline(self, is_host=False)

    def showTitleImage(self, visible: bool) -> None:
        if visible:
            self.title_np.show()
        else:
            self.title_np.hide()

    def openTitle(self) -> None:
        self.title_init.closeScreen()
        self.title.openScreen()