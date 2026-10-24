import os
import subprocess
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def rodar_arquivo(nome_arquivo: str, *args: str):
    caminho = os.path.join(BASE_DIR, nome_arquivo)

    if not os.path.exists(caminho):
        print(f"Arquivo não encontrado: {nome_arquivo}")
        return

    subprocess.run([sys.executable, caminho, *args], cwd=BASE_DIR)


def mostrar_menu():
    print("=" * 45)
    print("EVAN OS 1.2")
    print("Edivan Virtual Assistente Nativo")
    print("=" * 45)
    print()
    print("Escolha o modo de funcionamento:")
    print()
    print("1 - Modo texto")
    print("2 - Modo voz com ENTER")
    print("3 - Modo voz contínua")
    print("4 - Modo visual com rosto")
    print("5 - Treinar EVAN")
    print("6 - Testar microfone")
    print("7 - Aprender PDFs")
    print("8 - Configurar microfone")
    print("0 - Sair")
    print()


def main():
    while True:
        mostrar_menu()

        escolha = input("Escolha: ").strip()

        if escolha == "1":
            rodar_arquivo("main.py", "--modo", "texto")

        elif escolha == "2":
            rodar_arquivo("main.py", "--modo", "voz")

        elif escolha == "3":
            rodar_arquivo("main.py", "--modo", "voz-continua")

        elif escolha == "4":
            rodar_arquivo("main.py", "--modo", "visual")

        elif escolha == "5":
            rodar_arquivo("treinar_evan.py")

        elif escolha == "6":
            rodar_arquivo("testar_microfone.py")

        elif escolha == "7":
            rodar_arquivo("pdf_learning.py")

        elif escolha == "8":
            rodar_arquivo("mic_config.py")

        elif escolha == "0":
            print("Encerrando EVAN OS.")
            break

        else:
            print("Opção inválida.")

        input("\nPressione ENTER para voltar ao menu...")


if __name__ == "__main__":
    main()