import json

import sounddevice as sd

from config import SETTINGS_PATH


def listar_microfones():
    devices = sd.query_devices()
    microfones = []

    print("Microfones encontrados:\n")

    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            microfones.append(i)
            print(f"ID {i} - {device['name']}")
            print(f"  Canais de entrada: {device['max_input_channels']}")
            print(f"  Taxa padrão: {device['default_samplerate']}")
            print()

    return microfones


def salvar_configuracao(primary_id: int, backup_id: int):
    devices = sd.query_devices()
    settings = {
        "primary_mic_id": primary_id,
        "backup_mic_id": backup_id,
        # O nome vale mais que o número: os IDs mudam quando você abre o Steam,
        # pluga ou desplug algo. O EVAN procura o ID pelo nome a cada escuta.
        "primary_mic_name": devices[primary_id]["name"],
        "backup_mic_name": devices[backup_id]["name"],
    }

    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4, ensure_ascii=False)

    print("\nConfiguração salva com sucesso.")
    print(f"Microfone principal: ID {primary_id} - {settings['primary_mic_name']}")
    print(f"Microfone reserva: ID {backup_id} - {settings['backup_mic_name']}")


def main():
    microfones = listar_microfones()

    print("Dica: escolha microfones reais (ELITE 06, Captain 300...).")
    print("Evite 'Steam Streaming' e 'Mapeador de som'. Use IDs da lista acima.")
    print()

    primary = input("Digite o ID do microfone principal: ").strip()
    backup = input("Digite o ID do microfone reserva: ").strip()

    try:
        primary_id = int(primary)
        backup_id = int(backup)
    except ValueError:
        print("ID inválido. Digite apenas números.")
        return

    if primary_id not in microfones:
        print("O ID principal não parece ser um microfone válido.")
        return

    if backup_id not in microfones:
        print("O ID reserva não parece ser um microfone válido.")
        return

    salvar_configuracao(primary_id, backup_id)


if __name__ == "__main__":
    main()