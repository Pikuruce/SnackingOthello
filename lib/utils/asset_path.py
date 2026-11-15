from pathlib import Path
import yaml
import json
from typing import Any
import sys
from panda3d.core import Filename

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
ASSET_DIR = PROJECT_DIR / "assets"

with open(PROJECT_DIR / "config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

CHARACTER_DIR = ASSET_DIR / config["assets"][0]
IMAGE_DIR = ASSET_DIR / config["assets"][1]
OBJECT_DIR = ASSET_DIR / config["assets"][2]
SOUND_DIR = ASSET_DIR / config["assets"][3]
FONT_DIR = ASSET_DIR / config["assets"][4]
REPLAY_DIR = ASSET_DIR / config["assets"][5]

def characterPath(character_name: str) -> tuple[Filename, dict[str, Any]]:
    character_dir = CHARACTER_DIR / character_name

    image_file = character_dir / f"{character_name}.png"
    json_file = character_dir / f"{character_name}.json"

    with open(json_file, encoding="utf-8") as f:
        json_data = json.load(f)

    image_path = Filename.fromOsSpecific(str(image_file))

    return image_path, json_data

def characterShadowPath() -> Filename:
    shadow_file = CHARACTER_DIR / "Shadow.png"
    shadow_path = Filename.fromOsSpecific(str(shadow_file))
    return shadow_path

def imagePath(*parts: str) -> Filename:
    return Filename.fromOsSpecific(str(IMAGE_DIR.joinpath(*parts)))

def objectPath(object_name: str) -> Filename:
    object_dir = OBJECT_DIR

    model_file = object_dir / f"{object_name}.obj"

    model_path = Filename.fromOsSpecific(str(model_file))

    return model_path

def bgmPath(*parts: str) -> Filename:
    bgm_dir = SOUND_DIR / "bgm"
    return Filename.fromOsSpecific(str(bgm_dir.joinpath(*parts)))

def sePath(*parts: str) -> Filename:
    se_dir = SOUND_DIR / "se"
    return Filename.fromOsSpecific(str(se_dir.joinpath(*parts)))

def motionData() -> dict:
    motion_file = CHARACTER_DIR / "animation.json"

    with open(motion_file, encoding="utf-8") as f:
        json_data = json.load(f)

    return listToTupleHook(json_data)

def fontFile() -> str:
    font = FONT_DIR / "DotGothic16-Regular.ttf"
    return Filename.fromOsSpecific(str(font)).getFullpath()

# JSONをパースする際、末端のリストが「すべて数値」かつ「長さが2」ならタプルに変換する関数
def listToTupleHook(obj):
    for key, value in obj.items():
        if isinstance(value, dict):
            continue  # さらに深いネストは再帰的に処理されるためスルー

        if isinstance(value, list):
            new_list = []
            for item in value:
                # 要素が [数値, 数値] の形（リスト）であればタプルに変換
                if isinstance(item, list) and all(
                    isinstance(x, (int, float)) for x in item
                ):
                    new_list.append(tuple(item))
                else:
                    new_list.append(item)
            obj[key] = new_list
    return obj

def getSaveDirectory() -> Path:
    if getattr(sys, "frozen", False):
        # exeとして実行している場合
        base_dir = Path(sys.executable).parent
    else:
        # Pythonスクリプトとして実行している場合
        base_dir = Path(__file__).resolve().parents[2]

    save_dir = base_dir / "snacking_othello_saves"
    save_dir.mkdir(parents=True, exist_ok=True)

    return save_dir

def getReplay() -> dict:
    replay_file = REPLAY_DIR / "tutorial_replay.json"
    with open(replay_file, encoding="utf-8") as f:
        json_data = json.load(f)
    return json_data