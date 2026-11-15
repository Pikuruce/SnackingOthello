from pathlib import Path
import yaml

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

with open(PROJECT_DIR / "config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def getVersion() -> str:
    return config["version"]

def getWindowConfig() -> dict:
    return config["window"]

def getAudioConfig() -> dict:
    return config["audio"]
