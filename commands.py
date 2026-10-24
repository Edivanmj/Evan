import re

from utils import normalize_text


_VOICE_COMMANDS = {
    "oi": "oi",
    "ola": "oi",
    "missao": "qual sua missao",
    "qual missao": "qual sua missao",
    "objetivo": "qual seu objetivo",
    "qual objetivo": "qual seu objetivo",
    "agir": "como voce deve agir",
    "como voce": "como voce deve agir",
    "estudar": "o que voce deve me ajudar a estudar",
    "estudos": "o que voce deve me ajudar a estudar",
    "corpo": "como sera seu corpo robotico",
    "corpo robotico": "como sera seu corpo robotico",
    "memoria": "memorias",
    "memorias": "memorias",
    "status": "status",
    "estado": "status",
    "estados": "status",
    "estatua": "status",
    "sistema": "status",
    "painel": "status",
    "painel do sistema": "status",
    "estado do sistema": "status",
    "ver sistema": "status",
    "diario": "diario",
    "sair": "sair",
    "fechar": "sair",
    "parar": "sair",
    "encerrar": "sair",
    "tchau": "sair",
    "adeus": "sair",
}

_NAME_PATTERN = re.compile(r"^\s*(?:e\s*van|evan|ivan|eva|eban)\b[\s,:;-]*", re.IGNORECASE)


# Palavras que o modelo de voz costuma escrever com acento.
_ACCENTED = {
    "missao": "missão",
    "memoria": "memória",
    "memorias": "memórias",
    "diario": "diário",
    "ola": "olá",
    "voce": "você",
    "robotico": "robótico",
}
_NAMES = ("eva", "evan")


def voice_grammar() -> list[str]:
    """Frases que o reconhecedor de voz deve aceitar (comandos + nome do EVAN).

    Com vocabulário fechado, o Vosk erra bem menos em palavras curtas.
    """
    phrases = set(_NAMES)
    for command in _VOICE_COMMANDS:
        variants = {command}
        accented = " ".join(_ACCENTED.get(word, word) for word in command.split())
        variants.add(accented)
        for variant in variants:
            phrases.add(variant)
            for name in _NAMES:
                phrases.add(f"{name} {variant}")
    return sorted(phrases) + ["[unk]"]


def corrigir_comando_por_voz(texto: str) -> str:
    normalizado = normalize_text(texto)

    if normalizado in _VOICE_COMMANDS:
        return _VOICE_COMMANDS[normalizado]
    if "missao" in normalizado:
        return "qual sua missao"
    if "objetivo" in normalizado:
        return "qual seu objetivo"
    if "agir" in normalizado:
        return "como voce deve agir"
    if "estudar" in normalizado or "estudos" in normalizado:
        return "o que voce deve me ajudar a estudar"
    if "corpo" in normalizado:
        return "como sera seu corpo robotico"
    if any(word in normalizado.split() for word in ("status", "estado", "sistema", "painel")):
        return "status"
    return texto


def remover_nome_evan(texto: str) -> str:
    return _NAME_PATTERN.sub("", texto, count=1).strip()


def chamou_evan(texto: str) -> bool:
    return _NAME_PATTERN.match(texto) is not None


def show_help() -> str:
    return (
        "Comandos disponíveis: sair, aprenda que ..., lembre que ..., "
        "guarde que ..., corrija: ..."
    )
