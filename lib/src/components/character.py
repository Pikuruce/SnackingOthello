from pathlib import Path
import math
from direct.showbase.ShowBase import ShowBase
import lib.utils.asset_path as path
from lib.src.components.sprite_animator import SpriteAnimator
from lib.src.composables.component_base import ComponentBase
from panda3d.core import (
    CardMaker,
    NodePath,
    TransparencyAttrib,
)


class Character(ComponentBase):
    def __init__(
        self,
        base: ShowBase,
        name: str,
        with_shadow: bool = False,
        is_two_sided: bool = False,
        face_camera_full: bool = False
    ) -> None:
        super().__init__(base, name)

        self.is_two_sided = is_two_sided
        self.face_camera_full = face_camera_full

        self.animator = None
        self.camera = None

        self.model = self.loadModel(name)

        self.model.reparentTo(self.node)

        self.shadow_node: NodePath | None = None
        if with_shadow:
            self.shadow_node = self.loadShadow(name)

    def loadModel(self, name: str) -> NodePath:
        """
        キャラクターの画像とアニメーション情報を読み込む。
        """
        super().loadModel()

        image_path, json_data = path.characterPath(name)

        file_path = Path(image_path.toOsSpecific())
        if not file_path.is_file():
            raise FileNotFoundError(
                f"Character image not found: {file_path}"
            )

        texture = self.loader.loadTexture(image_path)
        if texture is None:
            raise RuntimeError(
                f"Failed to load character texture: {image_path}"
            )

        card_maker = CardMaker(name)
        card_maker.setFrame(-0.5, 0.5, 0.0, 1.0)

        model = self.node.attachNewNode(card_maker.generate())
        model.setTexture(texture)
        model.setTwoSided(self.is_two_sided)
        model.setTransparency(TransparencyAttrib.MAlpha)

        self.animator = SpriteAnimator(
            model,
            name,
            json_data,
        )

        self.animator.play("front", "idle")

        return model

    def loadShadow(self, name: str) -> NodePath:
        """
        キャラクターの影を読み込む。
        """
        shadow_path = path.characterShadowPath()

        file_path = Path(shadow_path.toOsSpecific())
        if not file_path.is_file():
            raise FileNotFoundError(
                f"Character shadow not found: {file_path}"
            )

        texture = self.loader.loadTexture(shadow_path)
        if texture is None:
            raise RuntimeError(
                f"Failed to load character shadow: {shadow_path}"
            )

        card_maker = CardMaker(f"{name}_shadow")
        card_maker.setFrame(-0.3, 0.3, -0.3, 0.3)

        shadow = self.node.attachNewNode(card_maker.generate())
        shadow.setP(-90)
        shadow.setPos(0, 0.05, 0.01)
        shadow.setTexture(texture)
        shadow.setTransparency(TransparencyAttrib.MAlpha)

        return shadow

    def faceCamera(self) -> None:
        """
        2Dモデル用

        セットされたカメラに方向を向ける
        """

        if self.camera is None:
            return

        # カメラとキャラクターの座標（共通の親ノード基準）
        camera_pos = self.camera.getPos(self.node.getParent())
        character_pos = self.node.getPos(self.node.getParent())

        dx = camera_pos.x - character_pos.x
        dy = camera_pos.y - character_pos.y
        dz = camera_pos.z - character_pos.z

        # 水平方向の角度
        heading = math.degrees(math.atan2(dx, -dy))

        if self.face_camera_full:
            # 水平方向の距離
            horizontal_distance = math.sqrt(dx * dx + dy * dy)

            # 上下方向の角度
            pitch = -math.degrees(
                math.atan2(dz, horizontal_distance)
            )

            self.model.setHpr(heading, pitch, 0)
        else:
            self.model.setH(heading)

    def playAnimation(self, direction: str, animation: str, loop: bool = True) -> None:
        """
        アニメーションの再生
        """
        self.animator.play(direction, animation, loop)

    def getAnimation(self) -> tuple[str, str]:
        """
        現在流れているアニメーションを取得
        """
        return (self.animator.direction, self.animator.motion)

    def setShadowVisible(self, visible: bool) -> None:
        """
        影の表示・非表示切り替え
        """
        if self.shadow_node is None:
            return

        if visible:
            self.shadow_node.show()
        else:
            self.shadow_node.hide()

    def setShadowPos(self, x, y, z) -> None:
        """
        影の位置設定
        """
        if self.shadow_node is not None:
            self.shadow_node.setPos(x, y, z)

    def setCamera(self, cam) -> None:
        """
        カメラを登録
        """
        self.camera = cam

    def update(self, dt: float) -> None:
        """
        更新処理
        """
        super().update(dt)
        if self.animator is not None:
            self.animator.update(dt)

        if self.camera is not None:
            self.faceCamera()
