# Modos de execução do EVAN OS (texto, voz com ENTER, voz contínua, visual)
from brain import EvanBrain
from commands import chamou_evan, corrigir_comando_por_voz, remover_nome_evan, voice_grammar
from utils import log_event, normalize_text

EXIT_WORDS = {"sair", "fechar", "parar", "encerrar", "tchau", "adeus"}
GRAMMAR = voice_grammar()


def _is_exit(command: str) -> bool:
    return normalize_text(command) in EXIT_WORDS


def _farewell(brain: EvanBrain) -> str:
    memory = brain.memory.find_similar_memory("fato", "meu nome")
    name = memory["valor"].strip() if memory else ""
    name = name or "Edivan"
    return f"Até logo, {name}."


def _answer(brain: EvanBrain, voice, command: str) -> bool:
    """Responde um comando. Retorna False quando for hora de encerrar."""
    if _is_exit(command):
        farewell = _farewell(brain)
        print(f"EVAN: {farewell}")
        voice.speak(farewell)
        log_event(f"EVAN: {farewell}")
        return False

    response = brain.handle(command)
    print(f"EVAN: {response}\n")
    log_event(f"EVAN: {response}")
    voice.speak(response)
    return True


def _listen_command(
    hearing, voice, face, first_seconds, second_seconds, require_name, use_grammar=True
):
    """Escuta uma fala e devolve o comando já corrigido ('' se não houve)."""
    listen_args = {"grammar": GRAMMAR} if use_grammar else {}
    print("Ouvindo... diga EVAN ou EVA para me chamar.")
    if face:
        face.listening()
    user_text = hearing.listen_once(seconds=first_seconds, **listen_args)
    if face:
        face.idle()
    if not user_text:
        return ""

    print(f"Ouvi: {user_text}")
    log_event(f"Voz detectada: {user_text}")

    if chamou_evan(user_text):
        command = remover_nome_evan(user_text)
    elif require_name:
        ajustado = corrigir_comando_por_voz(user_text)
        if ajustado == user_text:
            print("Ignorado. Meu nome não foi chamado.\n")
            return ""
        command = ajustado
    else:
        command = user_text

    if not command:
        print("EVAN: Estou ouvindo. Pode falar o comando.")
        voice.speak("Estou ouvindo.")
        if face:
            face.listening()
        command = hearing.listen_once(seconds=second_seconds, **listen_args)
        if face:
            face.idle()
        command = remover_nome_evan(command or "")
        if not command:
            print("EVAN: Não consegui entender o comando.\n")
            voice.speak("Não consegui entender o comando.")
            return ""
        print(f"Comando após chamada: {command}")

    corrected = corrigir_comando_por_voz(command)
    print(f"Comando entendido: {corrected}")
    log_event(f"Comando por voz: {corrected}")
    return corrected

def run_text() -> None:
    from conversation import ConversationLoop

    ConversationLoop().run()


def run_voice_enter() -> None:
    from hearing import EvanHearing
    from voice import EvanVoice

    brain, hearing, voice = EvanBrain(), EvanHearing(), EvanVoice()
    print("EVAN OS - Modo Voz")
    print("Pressione ENTER para falar. Fale 'sair' para encerrar.\n")
    voice.speak("Modo voz iniciado. Pressione enter para falar comigo.")

    while True:
        input("Pressione ENTER para falar...")
        user_text = hearing.listen_once(seconds=7)
        if not user_text:
            print("EVAN: Não consegui entender. Tente falar de novo.")
            voice.speak("Não consegui entender. Tente falar de novo.")
            continue

        command = corrigir_comando_por_voz(user_text)
        print(f"Você disse: {user_text}")
        if command != user_text:
            print(f"Comando ajustado: {command}")
        log_event(f"Usuário por voz: {user_text} -> {command}")

        if not _answer(brain, voice, command):
            break


def run_voice_continuous() -> None:
    from hearing import EvanHearing
    from voice import EvanVoice

    brain, hearing, voice = EvanBrain(), EvanHearing(), EvanVoice()
    print("EVAN OS - Modo Voz Contínua")
    print("Diga 'EVAN' ou 'EVA' antes do comando. 'EVA sair' encerra.\n")
    voice.speak("Modo voz contínua iniciado. Diga eva antes do comando.")

    while True:
        command = _listen_command(hearing, voice, None, 6, 4, require_name=True)
        if command and not _answer(brain, voice, command):
            break


def run_visual() -> None:
    from face import EvanFace
    from hearing import EvanHearing
    from voice import EvanVoice

    face = EvanFace()
    face.start()
    try:
        brain, hearing, voice = EvanBrain(), EvanHearing(), EvanVoice(face=face)
        print("EVAN OS - Modo Visual")
        print("Diga 'EVA' antes do comando. 'EVA sair' encerra.\n")
        voice.speak("Modo visual iniciado. Diga eva antes do comando.")

        while True:
            command = _listen_command(hearing, voice, face, 5, 6, require_name=False)
            if command and not _answer(brain, voice, command):
                break
    finally:
        face.close()


MODES = {
    "texto": run_text,
    "voz": run_voice_enter,
    "voz-continua": run_voice_continuous,
    "visual": run_visual,
}
