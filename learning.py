from utils import normalize_text


LEARNING_COMMANDS = [
    "aprenda que",
    "lembre que",
    "guarde que"
]

CORRECTION_COMMANDS = [
    "corrija:",
    "corrige:",
    "corrigir:"
]


def is_learning_command(text: str) -> bool:
    lowered = text.lower().strip()
    return any(lowered.startswith(cmd) for cmd in LEARNING_COMMANDS)


def is_correction_command(text: str) -> bool:
    lowered = text.lower().strip()
    return any(lowered.startswith(cmd) for cmd in CORRECTION_COMMANDS) or "o certo é" in lowered


def remove_learning_command(text: str) -> str:
    lowered = text.lower().strip()

    for cmd in LEARNING_COMMANDS:
        if lowered.startswith(cmd):
            return text[len(cmd):].strip()

    return text.strip()


def detect_key_and_value(content: str) -> dict:
    original = content.strip()
    normalized = normalize_text(original)

    # Caso especial: meu nome
    if "meu nome e" in normalized or "meu nome é" in normalized:
        if " é " in original:
            value = original.split(" é ", 1)[1].strip()
        elif " e " in normalized:
            # fallback simples
            value = original.split(" e ", 1)[1].strip()
        else:
            value = original

        return {
            "tipo": "fato",
            "chave": "meu nome",
            "valor": value
        }

    # Caso: EVAN significa alguma coisa
    if " significa " in normalized:
        parts = original.split(" significa ", 1)
        if len(parts) == 2:
            return {
                "tipo": "fato",
                "chave": parts[0].strip(),
                "valor": original
            }

    # Caso: EVAN não é ...
    if " não é " in original.lower() or " nao e " in normalized:
        subject = original.split(" não é ", 1)[0].strip() if " não é " in original.lower() else original.split(" nao e ", 1)[0].strip()
        return {
            "tipo": "fato",
            "chave": subject,
            "valor": original
        }

    # Caso: EVAN é ...
    if " é " in original:
        subject = original.split(" é ", 1)[0].strip()
        return {
            "tipo": "fato",
            "chave": subject,
            "valor": original
        }

    # Caso sem acento: EVAN e ...
    if " e " in normalized:
        words = original.split()
        if len(words) >= 2:
            return {
                "tipo": "fato",
                "chave": words[0],
                "valor": original
            }

    # Padrão: salva a frase inteira
    words = original.split()
    key = " ".join(words[:3]) if words else "geral"

    return {
        "tipo": "fato",
        "chave": key,
        "valor": original
    }


def parse_learning_content(text: str):
    content = remove_learning_command(text)

    if not content:
        return None

    return detect_key_and_value(content)


def parse_correction(text: str):
    lowered = text.lower().strip()

    if "o certo é" in lowered:
        content = text.split("o certo é", 1)[1].strip()
        return detect_key_and_value(content)

    for cmd in CORRECTION_COMMANDS:
        if lowered.startswith(cmd):
            content = text.split(":", 1)[1].strip()
            return detect_key_and_value(content)

    return None