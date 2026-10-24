# Loop principal de conversa do EVAN

from brain import EvanBrain
from utils import log_event
from voice import EvanVoice


class ConversationLoop:
    def __init__(self):
        self.brain = EvanBrain()
        self.voice = EvanVoice()

    def run(self):
        print("EVAN OS - Assistente offline")
        print("Digite 'sair' para encerrar.\n")

        while True:
            user_input = input("Você: ").strip()

            if user_input.lower() == "sair":
                response = "Até logo!"
                print(f"EVAN: {response}")
                log_event(f"EVAN: {response}")
                self.voice.speak(response)
                break

            response = self.brain.handle(user_input)

            print(f"EVAN: {response}")
            log_event(f"Usuário: {user_input}")
            log_event(f"EVAN: {response}")

            self.voice.speak(response)