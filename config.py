# Configurações centrais do projeto EVAN OS
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
PDF_DIR = BASE_DIR / "pdfs"
DB_PATH = DATA_DIR / "evan_memory.db"
LOG_PATH = LOGS_DIR / "evan.log"
SETTINGS_PATH = DATA_DIR / "evan_settings.json"
VOSK_MODEL_PATH = BASE_DIR / "models" / "vosk-model-small-pt-0.3"

NAME = "EVAN"
VERSION = "0.1"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
