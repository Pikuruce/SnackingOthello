
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
import lib.utils.asset_path as path
from lib.src.composables.component_base import ComponentBase
from panda3d.core import (
    NodePath,
)


class Object(ComponentBase):
    def __init__(
        self,
        base: ShowBase,
        name: str,
    ) -> None:
        """
        3Dオブジェクトを生成する

        Args:
            base: ShowBase
            name: オブジェクト名
        """
        super().__init__(base, name)

        # モデルのロード
        self.model = self.loadModel(name)
        self.model.reparentTo(self.node)

    def loadModel(self, name: str) -> NodePath:
        """
        3Dモデルをロードする
        """
        super().loadModel()
        
        model_path = path.objectPath(name)

        file_path = Path(model_path.toOsSpecific())

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Model file not found: {file_path}"
            )

        model = self.loader.loadModel(
            model_path,
            noCache=True,
        )

        if model is None or model.isEmpty():
            raise RuntimeError(
                f"Model loading failed: {model_path}"
            )

        return model
