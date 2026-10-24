from brain import EvanBrain
from commands import chamou_evan, corrigir_comando_por_voz, remover_nome_evan
from hearing import EvanHearing
from utils import log_event, normalize_text
from voice import EvanVoice


def main():
    brain = EvanBrain()
    hearing = EvanHearing()
    voice = EvanVoice()

    print("EVAN OS - Modo Voz Contínua")
    print("Diga 'EVAN' ou 'EVA' antes do comando.")
    print("Também pode falar em duas partes: 'EVA' e depois 'missão'.")
    print("Diga 'EVA sair' para encerrar.\n")
    voice.speak("Modo voz contínua iniciado. Diga eva antes do comando.")

    while True:
        print("Ouvindo... diga EVAN ou EVA para me chamar.")
        user_text = hearing.listen_once(seconds=6)
        if not user_text:
            continue

        print(f"Ouvi: {user_text}")
        log_event(f"Voz detectada: {user_text}")
        if not chamou_evan(user_text):
            print("Ignorado. Meu nome não foi chamado.\n")
            continue

        command = remover_nome_evan(user_text)
        if not command:
            print("EVAN: Estou ouvindo. Pode falar o comando.")
            voice.speak("Estou ouvindo.")
            command = hearing.listen_once(seconds=4)
            if not command:
                print("EVAN: Não consegui entender o comando.\n")
                voice.speak("Não consegui entender o comando.")
                continue
            print(f"Comando após chamada: {command}")

        corrected_command = corrigir_comando_por_voz(command)
        print(f"Comando entendido: {corrected_command}")
        log_event(f"Comando por voz contínua: {corrected_command}")

        if normalize_text(corrected_command) in {
            "sair", "fechar", "parar", "encerrar", "tchau", "adeus"
        }:
            response = "Até logo, Edivan."
            print(f"EVAN: {response}")
            voice.speak(response)
            log_event(f"EVAN: {response}")
            break

        response = brain.handle(corrected_command)
        print(f"EVAN: {response}\n")
        log_event(f"EVAN: {response}")
        voice.speak(response)


if __name__ == "__main__":
    main()
