# Funções utilitárias reutilizáveis pelo projeto
import logging
import re
import unicodedata
from pathlib import Path

from config import LOG_PATH


def normalize_text(text: str) -> str:
    """Remove acentos, pontuação e espaços extras para facilitar comparações."""
    text = unicodedata.normalize("NFKD", text.lower().strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_punctuation(text: str) -> str:
    """Remove pontuação simples no final da frase."""
    return text.rstrip(" .,!?:;-")


def setup_logger():
    """Cria um logger simples para gravar eventos em disco."""
    logger = logging.getLogger("evan")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


LOGGER = setup_logger()


def log_event(message: str, level: str = "INFO"):
    """Registra mensagens no arquivo de log."""
    getattr(LOGGER, level.lower(), LOGGER.info)(message)
