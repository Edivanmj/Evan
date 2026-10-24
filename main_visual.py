from brain import EvanBrain
from commands import chamou_evan, corrigir_comando_por_voz, remover_nome_evan
from face import EvanFace
from hearing import EvanHearing
from utils import log_event, normalize_text
from voice import EvanVoice


def main():
    face = EvanFace()
    face.start()

    try:
        brain = EvanBrain()
        hearing = EvanHearing()
        voice = EvanVoice(face=face)

        print("EVAN OS - Modo Visual")
        print("Diga 'EVA' antes do comando.")
        print("Exemplo: 'EVA missão'")
        print("Diga 'EVA sair' para encerrar.\n")
        voice.speak("Modo visual iniciado. Diga eva antes do comando.")

        while True:
            print("Ouvindo... diga EVA para me chamar.")
            face.listening()
            user_text = hearing.listen_once(seconds=5)
            face.idle()

            if not user_text:
                continue

            print(f"Ouvi: {user_text}")
            log_event(f"Voz detectada no modo visual: {user_text}")

            if chamou_evan(user_text):
                command = remover_nome_evan(user_text)
            else:
                corrected_attempt = corrigir_comando_por_voz(user_text)
                if corrected_attempt == user_text:
                    print("Não ouvi meu nome, mas vou tentar entender mesmo assim.\n")
                    command = user_text
                else:
                    print("Comando entendido mesmo sem chamar meu nome.")
                    command = corrected_attempt

            if not command:
                print("EVAN: Estou ouvindo. Pode falar o comando.")
                voice.speak("Estou ouvindo.")
                face.listening()
                command = hearing.listen_once(seconds=6)
                face.idle()
                if not command:
                    print("EVAN: Não consegui entender o comando.\n")
                    voice.speak("Não consegui entender o comando.")
                    continue
                print(f"Comando após chamada: {command}")

            corrected_command = corrigir_comando_por_voz(command)
            print(f"Comando entendido: {corrected_command}")
            log_event(f"Comando visual entendido: {corrected_command}")

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
    finally:
        face.close()


if __name__ == "__main__":
    main()
