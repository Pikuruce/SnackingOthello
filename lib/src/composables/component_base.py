from typing import Callable
from direct.showbase.ShowBase import ShowBase
import lib.src.components.collider as col
from panda3d.core import (
    NodePath,
    BitMask32
)

class ComponentBase:
    def __init__(
        self,
        base: ShowBase,
        name: str,
    ) -> None:
        self.parent = base.render
        self.loader = base.loader
        self.name = name

        self.self_func: Callable | None = None

        self.collider = None
        
        self.init_pos = None
        self.continuous = True
        self.on_collision = False
        self.on_trigger = False

        self.model = None

        self.node = self.parent.attachNewNode(name)

    def loadModel(self):
        """
        拡張クラスで実装、モデルを読み込む
        """
        pass

    def createCollider(
        self,
        collision_type: str,
        debug: bool = False,
        sphere_size: tuple = (0, 0, 0.5, 0.45),
        box_size: tuple = (-1, -1, -1, 1, 1, 1),
        into_mask=BitMask32.bit(1),
    ) -> None:
        """
        コライダーを生成する
        """

        self.collider = col.Collider(
            parent=self.node,
            name=self.name,
            collision_type=collision_type,
            debug=debug,
            sphere_size=sphere_size,
            box_size=box_size,
            into_mask=into_mask,
        )

    def reparent(self, parent: NodePath) -> None:
        """
        オブジェクトの親ノードを変更する

        Args:
            parent: 新しい親ノード
        """
        self.node.reparentTo(parent)

    def setPos(self, x, y, z, init_pos: bool = False) -> None:
        """
        位置を設定
        """
        self.node.setPos(x, y, z)

        if init_pos:
            self.init_pos = self.node.getPos()

    def getPos(self):
        """
        位置を取得
        """
        return self.node.getPos()

    def setScale(
        self,
        x: float,
        y: float | None = None,
        z: float | None = None,
    ) -> None:
        """
        スケールを設定する
        """

        if y is None or z is None:
            self.node.setScale(x)
        else:
            self.node.setScale(x, y, z)

    def setRotate(self, h, p=0, r=0) -> None:
        """
        回転を設定する
        """
        self.node.setHpr(h, p, r)

    def getRotate(self):
        """
        回転を取得する
        """
        return self.node.getHpr()

    def setAnchor(self, x: float, y: float, z: float) -> None:
        """
        アンカーを設定する
        """
        if self.model != None:
            self.model.setPos(-x, -y, -z)

    def setContinuous(self, value: bool) -> None:
        """
        継続的にセットされた関数を呼ぶかどうかの設定
        """
        self.continuous = value

    def setSelfFunction(
        self,
        func: Callable,
        continuous: bool = True,
    ) -> None:
        """
        関数をセットする
        """
        self.self_func = func
        self.continuous = continuous

    def setOnTrigger(self, value: bool) -> None:
        """
        衝突状態を設定する
        """

        self.on_trigger = value

    def ignitionFunc(self, dt: float = 1.0) -> None:
        """
        オブジェクト固有の更新関数を実行する
        """

        if self.self_func is not None and self.on_trigger:
            self.self_func(self, dt)

    def update(self, dt: float) -> None:
        """
        オブジェクトを更新する
        """

        if self.continuous:
            self.ignitionFunc(dt)

    def remove(self) -> None:
        """
        削除する
        """
        self.node.removeNode()

    def hide(self) -> None:
        """
        非表示にする
        """
        self.model.hide()

    def show(self) -> None:
        """
        表示する
        """
        self.model.show()
