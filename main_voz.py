from brain import EvanBrain
from commands import corrigir_comando_por_voz
from hearing import EvanHearing
from voice import EvanVoice
from utils import log_event, normalize_text


def main():
    brain = EvanBrain()
    hearing = EvanHearing()
    voice = EvanVoice()

    print("EVAN OS - Modo Voz")
    print("Pressione ENTER para falar.")
    print("Fale 'sair' para encerrar.\n")

    voice.speak("Modo voz iniciado. Pressione enter para falar comigo.")

    while True:
        input("Pressione ENTER para falar...")

        user_text = hearing.listen_once(seconds=7)

        if not user_text:
            print("EVAN: Não consegui entender. Tente falar de novo.")
            voice.speak("Não consegui entender. Tente falar de novo.")
            continue

        comando_corrigido = corrigir_comando_por_voz(user_text)

        print(f"Você disse: {user_text}")

        if comando_corrigido != user_text:
            print(f"Comando ajustado: {comando_corrigido}")

        log_event(f"Usuário por voz: {user_text}")
        log_event(f"Comando ajustado: {comando_corrigido}")

        if normalize_text(comando_corrigido) in {
            "sair", "fechar", "parar", "encerrar", "tchau", "adeus"
        }:
            response = "Até logo, Edivan."
            print(f"EVAN: {response}")
            voice.speak(response)
            log_event(f"EVAN: {response}")
            break

        response = brain.handle(comando_corrigido)

        print(f"EVAN: {response}")
        log_event(f"EVAN: {response}")

        voice.speak(response)


if __name__ == "__main__":
    main()